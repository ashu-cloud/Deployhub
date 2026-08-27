from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.hmac_factory import github_headers, github_push_payload
from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token

pytestmark = pytest.mark.e2e

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_unsigned_webhook_is_rejected():
    base = await require_service("project")
    body = github_push_payload()
    async with live_client() as client:
        response = await client.post(
            f"{base}/webhooks/github/{uuid4()}",
            content=body,
            headers={"Content-Type": "application/json", "X-GitHub-Event": "push"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_wrong_signature_is_rejected():
    base = await require_service("project")
    body = github_push_payload()
    async with live_client() as client:
        response = await client.post(
            f"{base}/webhooks/github/{uuid4()}",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=" + ("ab" * 32),
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": str(uuid4()),
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_valid_signature_unknown_project_is_404():
    base = await require_service("project")
    body = github_push_payload()
    headers = github_headers(body)
    async with live_client() as client:
        response = await client.post(f"{base}/webhooks/github/{uuid4()}", content=body, headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_valid_push_queues_and_is_idempotent():
    project_base = await require_service("project")
    headers_auth = auth_header(make_access_token(USER))
    name = f"hook-{uuid4().hex[:8]}"
    body = github_push_payload()
    hook_headers = github_headers(body)

    async with live_client() as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers_auth,
            json={"repo_name": name, "repo_url": f"https://github.com/hook/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.text}")
        project_id = created.json()["id"]

        first = await client.post(
            f"{project_base}/webhooks/github/{project_id}",
            content=body,
            headers=hook_headers,
        )
        assert first.status_code == 200, first.text
        assert first.json()["status"] == "build_queued"
        assert first.json().get("deployment_id")

        second = await client.post(
            f"{project_base}/webhooks/github/{project_id}",
            content=body,
            headers=hook_headers,
        )
        assert second.status_code == 200
        assert second.json()["status"] == "ignored_duplicate"


@pytest.mark.asyncio
async def test_ping_event_ignored():
    base = await require_service("project")
    body = github_push_payload()
    headers = github_headers(body, event="ping")
    async with live_client() as client:
        response = await client.post(f"{base}/webhooks/github/{uuid4()}", content=body, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
