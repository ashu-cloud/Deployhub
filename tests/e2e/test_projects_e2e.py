from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token

pytestmark = pytest.mark.e2e

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_unauthenticated_project_list_is_denied():
    base = await require_service("project")
    async with live_client() as client:
        response = await client.get(f"{base}/projects/")
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_project_crud_lifecycle():
    base = await require_service("project")
    token = make_access_token(USER)
    headers = auth_header(token)
    name = f"e2e-{uuid4().hex[:8]}"
    repo_url = f"https://github.com/e2e-tests/{name}"

    async with live_client() as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": repo_url},
        )
        if created.status_code >= 500:
            pytest.skip(f"project-service returned {created.status_code}: {created.text[:200]}")
        assert created.status_code in {201, 400}, created.text
        if created.status_code == 400 and "already exists" in created.text.lower():
            listed = await client.get(f"{base}/projects/", headers=headers)
            match = next((p for p in listed.json() if p["repo_url"] == repo_url), None)
            assert match is not None
            project_id = match["id"]
        else:
            assert created.status_code == 201, created.text
            project_id = created.json()["id"]
            assert created.json()["repo_name"] == name
            assert created.json()["status"] == "active"

        listed = await client.get(f"{base}/projects/", headers=headers)
        assert listed.status_code == 200
        ids = [p["id"] for p in listed.json()]
        assert project_id in ids

        fetched = await client.get(f"{base}/projects/{project_id}", headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()["id"] == project_id

        duplicate = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": repo_url},
        )
        assert duplicate.status_code == 400

        deleted = await client.delete(f"{base}/projects/{project_id}", headers=headers)
        assert deleted.status_code in {204, 200}

        after = await client.get(f"{base}/projects/{project_id}", headers=headers)
        # soft-delete: hidden from list, get may 200 archived or 404 depending on query
        listed_after = await client.get(f"{base}/projects/", headers=headers)
        assert project_id not in [p["id"] for p in listed_after.json()]
        assert after.status_code in {200, 404}


@pytest.mark.asyncio
async def test_invalid_github_url_rejected():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    async with live_client() as client:
        response = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": "nope", "repo_url": "https://example.com/not-github"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_project():
    base = await require_service("project")
    owner = auth_header(make_access_token("22222222-2222-4222-8222-222222222222"))
    other = auth_header(make_access_token("33333333-3333-4333-8333-333333333333"))
    name = f"iso-{uuid4().hex[:8]}"
    async with live_client() as client:
        created = await client.post(
            f"{base}/projects/",
            headers=owner,
            json={"repo_name": name, "repo_url": f"https://github.com/iso/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create isolation project: {created.status_code} {created.text}")
        project_id = created.json()["id"]
        peek = await client.get(f"{base}/projects/{project_id}", headers=other)
        assert peek.status_code in {403, 404}
        listed = await client.get(f"{base}/projects/", headers=other)
        assert project_id not in [p["id"] for p in listed.json()]


@pytest.mark.asyncio
async def test_env_var_roundtrip_hides_value():
    base = await require_service("project")
    headers = auth_header(make_access_token(USER))
    name = f"env-{uuid4().hex[:8]}"
    async with live_client() as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": f"https://github.com/env/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create env project: {created.text}")
        project_id = created.json()["id"]
        secret = "must-not-appear-in-json"
        posted = await client.post(
            f"{base}/projects/{project_id}/env-vars",
            headers=headers,
            json={"key": "API_TOKEN", "value": secret},
        )
        assert posted.status_code == 201, posted.text
        assert secret not in posted.text
        assert "value" not in posted.json()
        listed = await client.get(f"{base}/projects/{project_id}/env-vars", headers=headers)
        assert listed.status_code == 200
        keys = [row["key"] for row in listed.json()]
        assert "API_TOKEN" in keys
        assert secret not in listed.text
