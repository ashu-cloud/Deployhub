from __future__ import annotations

from datetime import timedelta

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from tests.helpers.http import live_client, require_service, url_alive
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.service_loader import service_on_path
from tests.helpers.settings import SERVICES

pytestmark = pytest.mark.security


def test_unsigned_alg_none_token_is_rejected():
    from fastapi import HTTPException

    try:
        token = jwt.encode({"sub": "attacker"}, key=None, algorithm="none")
    except Exception:
        return
    if isinstance(token, bytes):
        token = token.decode()
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


def test_empty_bearer_token_is_rejected():
    from fastapi import HTTPException

    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_expired_and_forged_tokens_denied_live():
    if not await url_alive(SERVICES["project"]):
        from tests.helpers.http import skip_or_fail

        skip_or_fail("project service is not reachable")
    base = SERVICES["project"]
    expired = make_access_token("user-1", expires_delta=timedelta(minutes=-30))
    forged = make_access_token("user-1", secret="wrong-secret-value-not-used")
    async with live_client() as client:
        r1 = await client.get(f"{base}/projects/", headers=auth_header(expired))
        r2 = await client.get(f"{base}/projects/", headers=auth_header(forged))
        r3 = await client.get(f"{base}/projects/", headers={"Authorization": "Bearer"})
        r4 = await client.get(f"{base}/projects/")
    assert r1.status_code in {401, 403}
    assert r2.status_code in {401, 403}
    assert r3.status_code in {401, 403, 422}
    assert r4.status_code in {401, 403}


@pytest.mark.asyncio
async def test_mutating_project_routes_require_auth():
    base = await require_service("project")
    pid = "00000000-0000-4000-8000-000000000000"
    async with live_client() as client:
        create = await client.post(f"{base}/projects/", json={"repo_name": "x", "repo_url": "https://github.com/a/b"})
        delete = await client.delete(f"{base}/projects/{pid}")
        deploy = await client.post(f"{base}/projects/{pid}/deploy")
        env = await client.post(f"{base}/projects/{pid}/env-vars", json={"key": "K", "value": "v"})
    for response in (create, delete, deploy, env):
        assert response.status_code in {401, 403, 404, 422}
        assert response.status_code != 201
        assert response.status_code != 204 or delete.status_code != 204
    assert create.status_code in {401, 403}
    assert deploy.status_code in {401, 403}
    assert env.status_code in {401, 403}
