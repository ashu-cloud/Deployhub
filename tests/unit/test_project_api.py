from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.mocks import make_project, mock_session
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit

USER_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _mock_rate_limit_redis():
    """create_project is rate-limited via Redis; keep these unit tests hermetic."""
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock(return_value=True)
    return patch("app.core.rate_limit.redis_client", mock_redis)


async def _project_client(session, token: str | None = None):
    with service_on_path("project-service"):
        from app.core.db import get_db
        from app.main import app

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        headers = auth_header(token or make_access_token(USER_A))
        transport = asgi_transport(app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
                yield client, app
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health():
    with service_on_path("project-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_projects_requires_auth():
    with service_on_path("project-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/projects/")
        assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_list_projects_returns_rows_for_caller():
    project = make_project(user_id=USER_A)
    session = mock_session(first=project, all_items=[project])
    async for client, _app in _project_client(session):
        response = await client.get("/projects/")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert body[0]["repo_name"] == project.repo_name


@pytest.mark.asyncio
async def test_create_project_rejects_non_github_url():
    session = mock_session(first=None)
    async for client, _app in _project_client(session):
        with _mock_rate_limit_redis():
            response = await client.post(
                "/projects/",
                json={"repo_url": "https://gitlab.com/acme/demo", "repo_name": "demo"},
            )
        assert response.status_code == 400
        assert "Invalid GitHub URL" in response.text


@pytest.mark.asyncio
async def test_create_project_rejects_duplicate():
    existing = make_project(user_id=USER_A)
    session = mock_session(first=existing)
    async for client, _app in _project_client(session):
        with _mock_rate_limit_redis():
            response = await client.post(
                "/projects/",
                json={"repo_url": existing.repo_url, "repo_name": existing.repo_name},
            )
        assert response.status_code == 400
        assert "already exists" in response.text.lower()


@pytest.mark.asyncio
async def test_create_project_success_registers_webhook():
    session = mock_session(first=None)

    async def refresh(obj):
        if not getattr(obj, "id", None):
            obj.id = uuid4()
        obj.status = getattr(obj, "status", None) or "active"
        obj.created_at = __import__("datetime").datetime.utcnow()
        if getattr(obj, "user_id", None) and not hasattr(obj.user_id, "hex"):
            from uuid import UUID

            obj.user_id = UUID(str(obj.user_id))

    session.refresh = refresh
    async for client, _app in _project_client(session):
        with _mock_rate_limit_redis(), patch("app.api.projects.github_webhook_service") as hooks:
            hooks.register_webhook = AsyncMock(return_value="hook-99")
            response = await client.post(
                "/projects/",
                json={"repo_url": "https://github.com/acme/demo", "repo_name": "demo"},
            )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["repo_name"] == "demo"
        hooks.register_webhook.assert_awaited()


@pytest.mark.asyncio
async def test_get_project_404_when_missing():
    session = mock_session(first=None)
    async for client, _app in _project_client(session):
        response = await client.get(f"/projects/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_rejects_malformed_uuid():
    session = mock_session(first=None)
    async for client, _app in _project_client(session):
        response = await client.get("/projects/not-a-uuid")
        assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_delete_project_is_soft_delete():
    project = make_project(user_id=USER_A)
    session = mock_session(first=project)
    async for client, _app in _project_client(session):
        response = await client.delete(f"/projects/{project.id}")
        assert response.status_code == 204
        assert project.status == "archived"


@pytest.mark.asyncio
async def test_create_project_is_rate_limited_per_user():
    session = mock_session(first=None)
    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=999)  # already far past the limit
    mock_redis.expire = AsyncMock(return_value=True)
    async for client, _app in _project_client(session):
        with patch("app.core.rate_limit.redis_client", mock_redis):
            response = await client.post(
                "/projects/",
                json={"repo_url": "https://github.com/acme/rl", "repo_name": "rl"},
            )
        assert response.status_code == 429


@pytest.mark.asyncio
async def test_trigger_deployment_queues_kafka_event():
    project = make_project(user_id=USER_A)
    session = mock_session(first=project, all_items=[])

    async def refresh(obj):
        obj.id = getattr(obj, "id", None) or uuid4()
        obj.created_at = __import__("datetime").datetime.utcnow()
        obj.deployment_number = getattr(obj, "deployment_number", 1)

    session.refresh = refresh
    async for client, _app in _project_client(session):
        with patch("app.core.kafka.kafka_client") as kafka:
            kafka.send_event = AsyncMock()
            response = await client.post(f"/projects/{project.id}/deploy")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "queued"
        assert body["git_branch"] == "main"
        kafka.send_event.assert_awaited()
        args, kwargs = kafka.send_event.await_args
        topic = args[0] if args else kwargs.get("topic")
        assert topic == "build.queued"
