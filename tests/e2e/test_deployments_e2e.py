from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token

pytestmark = pytest.mark.e2e

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_trigger_deploy_then_list():
    project_base = await require_service("project")
    deploy_base = await require_service("deployment")
    headers = auth_header(make_access_token(USER))
    name = f"dep-{uuid4().hex[:8]}"

    async with live_client() as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": f"https://github.com/dep/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.text}")
        project_id = created.json()["id"]

        queued = await client.post(f"{project_base}/projects/{project_id}/deploy", headers=headers)
        assert queued.status_code == 200, queued.text
        body = queued.json()
        assert body["status"] == "queued"
        deployment_id = body["id"]

        listed = await client.get(f"{deploy_base}/deployments/{project_id}", headers=headers)
        assert listed.status_code == 200
        ids = [str(row.get("id") or row.get("deployment_id")) for row in listed.json()]
        assert deployment_id in ids

        detail = await client.get(f"{deploy_base}/deployments/detail/{deployment_id}", headers=headers)
        assert detail.status_code == 200
        assert str(detail.json()["id"]) == deployment_id


@pytest.mark.asyncio
async def test_rollback_of_queued_deployment_rejected():
    project_base = await require_service("project")
    deploy_base = await require_service("deployment")
    headers = auth_header(make_access_token(USER))
    name = f"rb-{uuid4().hex[:8]}"

    async with live_client() as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": f"https://github.com/rb/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.text}")
        project_id = created.json()["id"]
        queued = await client.post(f"{project_base}/projects/{project_id}/deploy", headers=headers)
        if queued.status_code != 200:
            pytest.skip(queued.text)
        deployment_id = queued.json()["id"]
        rolled = await client.post(f"{deploy_base}/deployments/{deployment_id}/rollback", headers=headers)
        assert rolled.status_code == 400


@pytest.mark.asyncio
async def test_deployment_routes_reject_missing_auth():
    """Deployment reads/writes require a JWT (see tests/security/test_authorization.py)."""
    base = await require_service("deployment")
    async with live_client() as client:
        response = await client.get(f"{base}/deployments/detail/{uuid4()}")
    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_unknown_deployment_404():
    base = await require_service("deployment")
    headers = auth_header(make_access_token(USER))
    async with live_client() as client:
        response = await client.get(f"{base}/deployments/detail/{uuid4()}", headers=headers)
    assert response.status_code == 404
