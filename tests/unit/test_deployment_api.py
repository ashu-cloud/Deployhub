from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.mocks import make_deployment, mock_session
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit

USER = "11111111-1111-4111-8111-111111111111"


async def _client(session):
    with service_on_path("deployment-service"):
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
async def test_health():
    with service_on_path("deployment-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_deployment_routes_reject_missing_auth():
    dep = make_deployment(status="live")
    session = mock_session(first=dep, all_items=[dep])
    async for client, _app in _client(session):
        listed = await client.get(f"/deployments/{dep.project_id}")
        detail = await client.get(f"/deployments/detail/{dep.id}")
        rollback = await client.post(f"/deployments/{dep.id}/rollback")
    for response in (listed, detail, rollback):
        assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_list_deployments():
    dep = make_deployment(status="live")
    session = mock_session(first=dep, all_items=[dep])
    headers = auth_header(make_access_token(USER))
    async for client, _app in _client(session):
        response = await client.get(f"/deployments/{dep.project_id}", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)


@pytest.mark.asyncio
async def test_deployment_detail_404():
    session = mock_session(first=None)
    headers = auth_header(make_access_token(USER))
    async for client, _app in _client(session):
        response = await client.get(f"/deployments/detail/{uuid4()}", headers=headers)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_rollback_rejects_non_live_deployment():
    dep = make_deployment(status="queued", s3_path="x")
    session = mock_session(first=dep)
    headers = auth_header(make_access_token(USER))
    async for client, _app in _client(session):
        response = await client.post(f"/deployments/{dep.id}/rollback", headers=headers)
        assert response.status_code == 400
        assert "not live" in response.text.lower() or "not found" in response.text.lower()


@pytest.mark.asyncio
async def test_rollback_rejects_missing_deployment():
    session = mock_session(first=None)
    headers = auth_header(make_access_token(USER))
    async for client, _app in _client(session):
        response = await client.post(f"/deployments/{uuid4()}/rollback", headers=headers)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_malformed_uuid_is_422():
    session = mock_session(first=None)
    headers = auth_header(make_access_token(USER))
    async for client, _app in _client(session):
        response = await client.get("/deployments/detail/nope", headers=headers)
        assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_websocket_rejects_missing_token():
    with service_on_path("deployment-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # httpx doesn't speak the WS protocol, but a plain GET against a
            # websocket-only route without a valid token must never be
            # treated as an authenticated connection.
            response = await client.get(f"/deployments/ws/{uuid4()}")
        assert response.status_code in {400, 403, 404, 405, 426}
