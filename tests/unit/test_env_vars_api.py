from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.mocks import make_env_var, make_project, mock_session
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit

USER_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


async def _client(session):
    with service_on_path("project-service"):
        from app.core.db import get_db
        from app.main import app

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        headers = auth_header(make_access_token(USER_A))
        transport = asgi_transport(app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
                yield client
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_env_var_requires_auth():
    with service_on_path("project-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/projects/{uuid4()}/env-vars",
                json={"key": "NODE_ENV", "value": "production"},
            )
        assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_create_env_var_does_not_echo_plaintext():
    project = make_project(user_id=USER_A)
    env = make_env_var(key="DATABASE_URL")
    # first execute: project lookup; second: existing env lookup
    session = mock_session(first=project)

    async def refresh(obj):
        obj.id = getattr(obj, "id", None) or uuid4()
        obj.created_at = __import__("datetime").datetime.utcnow()
        obj.key = getattr(obj, "key", "DATABASE_URL")

    session.refresh = refresh

    calls = {"n": 0}

    async def execute(_stmt):
        calls["n"] += 1
        result = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
        scalars = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
        if calls["n"] == 1:
            scalars.first.return_value = project
        else:
            scalars.first.return_value = None
        result.scalars.return_value = scalars
        return result

    session.execute.side_effect = execute

    async for client in _client(session):
        with patch("app.api.env_vars.encryption_service") as enc:
            enc.encrypt.return_value = "cipher-text"
            response = await client.post(
                f"/projects/{project.id}/env-vars",
                json={"key": "DATABASE_URL", "value": "postgres://secret"},
            )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["key"] == "DATABASE_URL"
    assert "value" not in body
    assert "encrypted_value" not in body
    assert "postgres://" not in response.text


@pytest.mark.asyncio
async def test_list_env_vars_hides_ciphertext():
    project = make_project(user_id=USER_A)
    env = make_env_var(key="API_KEY", encrypted_value="should-never-leak")
    calls = {"n": 0}

    async def execute(_stmt):
        calls["n"] += 1
        result = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
        scalars = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
        if calls["n"] == 1:
            scalars.first.return_value = project
            scalars.all.return_value = [project]
        else:
            scalars.first.return_value = env
            scalars.all.return_value = [env]
        result.scalars.return_value = scalars
        return result

    session = mock_session(first=project)
    session.execute.side_effect = execute
    async for client in _client(session):
        response = await client.get(f"/projects/{project.id}/env-vars")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body[0]["key"] == "API_KEY"
    assert "encrypted_value" not in body[0]
    assert "should-never-leak" not in response.text


@pytest.mark.asyncio
async def test_env_vars_404_when_project_missing():
    session = mock_session(first=None)
    async for client in _client(session):
        response = await client.get(f"/projects/{uuid4()}/env-vars")
    assert response.status_code == 404
