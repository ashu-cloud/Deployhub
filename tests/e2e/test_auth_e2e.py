from __future__ import annotations

import pytest

from tests.helpers.http import live_client, require_service

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_github_login_redirects_offsite():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/auth/github")
    assert response.status_code in {302, 307}
    assert "github.com/login/oauth/authorize" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_callback_without_code_rejected():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/auth/callback")
    assert response.status_code in {400, 422}


@pytest.mark.asyncio
async def test_callback_with_bogus_code_does_not_500():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/auth/callback", params={"code": "definitely-not-real"})
    assert response.status_code in {400, 401, 403, 422}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_me_endpoint_responds():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/auth/me")
    assert response.status_code in {200, 401}
    assert response.status_code < 500
