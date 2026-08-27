from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit


async def _client():
    with service_on_path("auth-service"):
        from app.main import app

        transport = asgi_transport(app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, app


@pytest.mark.asyncio
async def test_health():
    async for client, _app in _client():
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_github_login_redirects_to_github():
    async for client, _app in _client():
        response = await client.get("/auth/github", follow_redirects=False)
        assert response.status_code in {302, 307}
        location = response.headers["location"]
        assert location.startswith("https://github.com/login/oauth/authorize")
        assert "client_id=" in location
        assert "scope=user:email" in location


@pytest.mark.asyncio
async def test_callback_without_code_is_rejected():
    async for client, _app in _client():
        response = await client.get("/auth/callback")
        assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_callback_sets_refresh_cookie_and_returns_access_token():
    """Access token is handed back in JSON for the SPA to hold in memory
    (architecture: stored in memory, not localStorage). The *refresh* token
    -- not the access token -- is the one carried in an HttpOnly/Secure/
    SameSite=Strict cookie.
    """
    with service_on_path("auth-service"):
        from app.core.db import get_db
        from app.main import app
        from app.models import User

        user = User(github_id=42, email="dev@example.com", name="Dev")
        user.id = __import__("uuid").uuid4()

        session = AsyncMock()
        result = AsyncMock()
        scalars = AsyncMock()
        scalars.first = lambda: None
        result.scalars = lambda: scalars
        session.execute = AsyncMock(return_value=result)

        async def refresh(obj):
            obj.id = user.id
            obj.created_at = __import__("datetime").datetime.utcnow()

        session.refresh = refresh
        session.add = lambda *_a, **_k: None
        session.commit = AsyncMock()

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        try:
            with patch("app.api.auth.github_service") as gh:
                gh.get_access_token = AsyncMock(return_value="gho_test")
                gh.get_user_info = AsyncMock(
                    return_value={"id": 42, "email": "dev@example.com", "name": "Dev", "login": "dev"}
                )
                transport = asgi_transport(app)
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.get("/auth/callback", params={"code": "abc"})
            assert response.status_code == 200
            body = response.json()
            assert body["token_type"] == "bearer"
            assert body["access_token"]
            cookie = response.headers.get("set-cookie", "")
            assert "refresh_token=" in cookie
            assert "access_token=" not in cookie
            assert "HttpOnly" in cookie or "httponly" in cookie.lower()
            assert "samesite=strict" in cookie.lower()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_me_requires_auth():
    async for client, _app in _client():
        response = await client.get("/auth/me")
        assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_me_returns_profile_for_valid_token():
    with service_on_path("auth-service"):
        from app.core.db import get_db
        from app.core.security import create_access_token
        from app.main import app
        from app.models import User
        import uuid as _uuid

        user_id = _uuid.uuid4()
        user = User(github_id=42, email="dev@example.com", name="Dev")
        user.id = user_id

        result = AsyncMock()
        scalars = AsyncMock()
        scalars.first = lambda: user
        result.scalars = lambda: scalars
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        async def override_db():
            yield session

        app.dependency_overrides[get_db] = override_db
        try:
            token = create_access_token({"sub": str(user_id)})
            transport = asgi_transport(app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            body = response.json()
            assert body["id"] == str(user_id)
            assert body["email"] == "dev@example.com"
        finally:
            app.dependency_overrides.clear()
