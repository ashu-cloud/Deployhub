from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.http import live_client, require_service, skip_or_fail, url_alive
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.settings import SERVICES

pytestmark = pytest.mark.security


@pytest.mark.asyncio
async def test_project_get_is_scoped_to_token_subject():
    base = await require_service("project")
    owner = auth_header(make_access_token(str(uuid4())))
    other = auth_header(make_access_token(str(uuid4())))
    name = f"sec-{uuid4().hex[:8]}"
    async with live_client() as client:
        created = await client.post(
            f"{base}/projects/",
            headers=owner,
            json={"repo_name": name, "repo_url": f"https://github.com/sec/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.text}")
        project_id = created.json()["id"]
        other_get = await client.get(f"{base}/projects/{project_id}", headers=other)
        other_list = await client.get(f"{base}/projects/", headers=other)
        other_env = await client.get(f"{base}/projects/{project_id}/env-vars", headers=other)
        other_delete = await client.delete(f"{base}/projects/{project_id}", headers=other)
    assert other_get.status_code in {403, 404}
    assert project_id not in [p["id"] for p in other_list.json()]
    assert other_env.status_code in {403, 404}
    assert other_delete.status_code in {403, 404}


@pytest.mark.security_audit
@pytest.mark.asyncio
async def test_deployment_reads_require_auth():
    """Deployment list/detail/rollback currently have no JWT dependency."""
    if not await url_alive(SERVICES["deployment"]):
        skip_or_fail("deployment service is not reachable")
    base = SERVICES["deployment"]
    pid = str(uuid4())
    did = str(uuid4())
    async with live_client() as client:
        listed = await client.get(f"{base}/deployments/{pid}")
        detail = await client.get(f"{base}/deployments/detail/{did}")
        rollback = await client.post(f"{base}/deployments/{did}/rollback")
    assert listed.status_code in {401, 403}, (
        "SECURITY FINDING: GET /deployments/{project_id} is reachable without a JWT"
    )
    assert detail.status_code in {401, 403, 404}
    if detail.status_code == 404:
        # 404 without auth still confirms the route is public.
        pytest.fail("SECURITY FINDING: deployment detail is reachable without a JWT (got 404, not 401)")
    assert rollback.status_code in {401, 403}


@pytest.mark.security_audit
def test_websocket_log_stream_requires_auth_in_source():
    from tests.helpers.paths import SERVICES_DIR

    source = (SERVICES_DIR / "deployment-service" / "app" / "api" / "deployments.py").read_text(
        encoding="utf-8"
    )
    ws_fn = "websocket_deployment_logs"
    assert ws_fn in source
    # The websocket handler must authenticate before accept().
    block_start = source.index("@router.websocket")
    block = source[block_start : block_start + 800]
    assert "get_current_user" in block or "token" in block.lower() and "query" in block.lower(), (
        "SECURITY FINDING: WebSocket /deployments/ws/{id} accepts connections with no auth check"
    )
