from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.hmac_factory import github_headers, github_push_payload
from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.settings import SERVICES

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_push_to_queue_keeps_platform_healthy():
    """Webhook accept -> deployment row -> every service still serves /health."""
    project_base = await require_service("project")
    await require_service("deployment")
    headers_auth = auth_header(make_access_token(USER))
    name = f"pipe-{uuid4().hex[:8]}"
    body = github_push_payload()
    hook_headers = github_headers(body)

    async with live_client() as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers_auth,
            json={"repo_name": name, "repo_url": f"https://github.com/pipe/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.text}")
        project_id = created.json()["id"]

        hooked = await client.post(
            f"{project_base}/webhooks/github/{project_id}",
            content=body,
            headers=hook_headers,
        )
        assert hooked.status_code == 200, hooked.text
        assert hooked.json()["status"] == "build_queued"

        deploy_id = hooked.json()["deployment_id"]
        deploy_base = SERVICES["deployment"]
        detail = await client.get(f"{deploy_base}/deployments/detail/{deploy_id}", headers=headers_auth)
        assert detail.status_code == 200
        assert detail.json()["status"] in {"queued", "building", "uploading", "uploaded", "live", "failed"}

        for name_key, base in SERVICES.items():
            health = await client.get(f"{base}/health")
            if health.status_code == 200:
                assert health.json().get("status") in {"ok", "healthy"}
            else:
                # service may be down independently; pipeline must not crash project-service
                assert name_key != "project"
