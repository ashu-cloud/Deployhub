from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token

pytestmark = pytest.mark.security

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_malformed_uuid_paths_are_rejected():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    async with live_client() as client:
        response = await client.get(f"{base}/projects/not-a-uuid", headers=headers)
    assert response.status_code in {400, 404, 422}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_missing_body_fields_rejected():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    async with live_client() as client:
        r1 = await client.post(f"{base}/projects/", headers=headers, json={})
        r2 = await client.post(f"{base}/projects/", headers=headers, json={"repo_name": "only-name"})
        r3 = await client.post(
            f"{base}/projects/",
            headers={**headers, "Content-Type": "application/json"},
            content=b"not-json",
        )
    assert r1.status_code in {400, 422}
    assert r2.status_code in {400, 422}
    assert r3.status_code in {400, 422}


@pytest.mark.security_audit
@pytest.mark.asyncio
async def test_oversized_json_is_handled():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    huge = "n" * 200_000
    async with live_client() as client:
        response = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": huge, "repo_url": f"https://github.com/size/{huge[:20]}"},
        )
    assert response.status_code in {400, 413, 422}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_wrong_content_type_on_create():
    base = await require_service("project")
    headers = {**auth_header(make_access_token(USER)), "Content-Type": "text/plain"}
    async with live_client() as client:
        response = await client.post(f"{base}/projects/", headers=headers, content=b"hello")
    assert response.status_code in {400, 415, 422}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_method_not_allowed_on_health():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.post(f"{base}/health", json={})
    assert response.status_code in {405, 404, 400}
    assert response.status_code < 500


@pytest.mark.security_audit
@pytest.mark.asyncio
async def test_env_var_rejects_empty_key():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    async with live_client() as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": f"val-{uuid4().hex[:8]}", "repo_url": f"https://github.com/val/{uuid4().hex[:8]}"},
        )
        if created.status_code != 201:
            pytest.skip(created.text)
        project_id = created.json()["id"]
        response = await client.post(
            f"{base}/projects/{project_id}/env-vars",
            headers=headers,
            json={"key": "", "value": "x"},
        )
    # empty key should not be stored as a valid env var
    assert response.status_code in {201, 400, 422}
    if response.status_code == 201:
        pytest.fail("SECURITY FINDING: empty env var keys are accepted")
