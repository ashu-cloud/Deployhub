from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.hmac_factory import github_headers, github_push_payload
from tests.helpers.mocks import make_project, mock_session
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit

PROJECT_ID = uuid4()


async def _client(session):
    with service_on_path("project-service"):
        from app.core.db import get_db
        from app.main import app

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        transport = asgi_transport(app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                yield client, app
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_webhook_missing_signature_rejected():
    session = mock_session(first=None)
    body = github_push_payload()
    async for client, _app in _client(session):
        response = await client.post(
            f"/webhooks/github/{PROJECT_ID}",
            content=body,
            headers={"Content-Type": "application/json", "X-GitHub-Event": "push"},
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected():
    session = mock_session(first=None)
    body = github_push_payload()
    async for client, _app in _client(session):
        response = await client.post(
            f"/webhooks/github/{PROJECT_ID}",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=" + ("00" * 32),
                "X-GitHub-Event": "push",
            },
        )
        assert response.status_code == 400
        assert "Invalid signature" in response.text


@pytest.mark.asyncio
async def test_webhook_ignores_non_push_events():
    session = mock_session(first=None)
    body = github_push_payload()
    headers = github_headers(body, event="ping")
    async for client, _app in _client(session):
        response = await client.post(f"/webhooks/github/{PROJECT_ID}", content=body, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"


@pytest.mark.asyncio
async def test_webhook_ignores_duplicate_delivery():
    session = mock_session(first=None)
    body = github_push_payload()
    headers = github_headers(body)
    async for client, _app in _client(session):
        with patch("app.api.webhooks.redis_client") as redis:
            # `SET NX` returns None/False when the key already exists -- i.e.
            # another request already claimed this delivery id.
            redis.set = AsyncMock(return_value=None)
            response = await client.post(f"/webhooks/github/{PROJECT_ID}", content=body, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "ignored_duplicate"


@pytest.mark.asyncio
async def test_webhook_ignores_branch_deletion():
    project = make_project()
    session = mock_session(first=project)
    body = github_push_payload(commit_sha="0" * 40)
    headers = github_headers(body)
    async for client, _app in _client(session):
        with (
            patch("app.api.webhooks.redis_client") as redis,
            patch("app.api.webhooks.kafka_client") as kafka,
        ):
            redis.set = AsyncMock(return_value=True)
            kafka.send_event = AsyncMock()
            response = await client.post(f"/webhooks/github/{PROJECT_ID}", content=body, headers=headers)
        assert response.status_code == 200
        assert response.json()["reason"] == "branch deletion"
        kafka.send_event.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_unknown_project_404():
    session = mock_session(first=None)
    body = github_push_payload()
    headers = github_headers(body)
    async for client, _app in _client(session):
        with patch("app.api.webhooks.redis_client") as redis:
            redis.set = AsyncMock(return_value=True)
            # The 404 raised for an unknown project releases the delivery
            # claim so a legitimate GitHub retry is not swallowed.
            redis.delete = AsyncMock()
            response = await client.post(f"/webhooks/github/{PROJECT_ID}", content=body, headers=headers)
        assert response.status_code == 404
        redis.delete.assert_awaited()


@pytest.mark.asyncio
async def test_webhook_queues_build_for_valid_push():
    project = make_project()
    session = mock_session(first=project)

    async def refresh(obj):
        obj.id = getattr(obj, "id", None) or uuid4()

    session.refresh = refresh
    body = github_push_payload()
    headers = github_headers(body)
    async for client, _app in _client(session):
        with (
            patch("app.api.webhooks.redis_client") as redis,
            patch("app.api.webhooks.kafka_client") as kafka,
        ):
            redis.set = AsyncMock(return_value=True)
            kafka.send_event = AsyncMock()
            response = await client.post(f"/webhooks/github/{project.id}", content=body, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "build_queued"
        kafka.send_event.assert_awaited()
        redis.set.assert_awaited_once()
