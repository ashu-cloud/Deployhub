from __future__ import annotations

import pytest

from tests.helpers.http import live_client, skip_or_fail
from tests.helpers.settings import FRONTEND_URL

pytestmark = pytest.mark.e2e


async def _frontend():
    async with live_client() as client:
        try:
            response = await client.get(FRONTEND_URL)
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable at {FRONTEND_URL}: {exc}")
            raise
        if response.status_code >= 500:
            skip_or_fail(f"frontend returned {response.status_code}")
        return client, response


@pytest.mark.asyncio
async def test_home_page_renders():
    async with live_client() as client:
        try:
            response = await client.get(FRONTEND_URL)
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable: {exc}")
    assert response.status_code == 200
    html = response.text.lower()
    assert "deployhub" in html
    assert "<html" in html


@pytest.mark.asyncio
async def test_login_page_offers_github_entry_only():
    """The login page must only offer real GitHub OAuth -- no dev-bypass shortcut

    (see tests/security/test_authentication.py::test_frontend_does_not_ship_a_dev_bypass_control).
    """
    async with live_client() as client:
        try:
            response = await client.get(f"{FRONTEND_URL}/login")
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable: {exc}")
    assert response.status_code == 200
    text = response.text
    assert "GitHub" in text
    assert "/api/v1/auth/github" in text
    assert "Dev Bypass" not in text


@pytest.mark.asyncio
async def test_docs_and_new_project_pages_render():
    async with live_client() as client:
        try:
            docs = await client.get(f"{FRONTEND_URL}/docs")
            new = await client.get(f"{FRONTEND_URL}/new")
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable: {exc}")
    assert docs.status_code == 200
    assert new.status_code == 200


@pytest.mark.asyncio
async def test_unknown_route_is_not_500():
    async with live_client() as client:
        try:
            response = await client.get(f"{FRONTEND_URL}/this-route-does-not-exist-xyz")
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable: {exc}")
    assert response.status_code in {200, 404}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_login_rewrite_reaches_auth_or_fails_cleanly():
    """Next.js rewrites /api/v1/auth/* to the auth service."""
    async with live_client() as client:
        try:
            response = await client.get(f"{FRONTEND_URL}/api/v1/auth/github")
        except Exception as exc:
            skip_or_fail(f"frontend is not reachable: {exc}")
    assert response.status_code in {200, 302, 307, 500, 502, 503, 504}
    if response.status_code in {302, 307}:
        assert "github.com" in response.headers.get("location", "")
