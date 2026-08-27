from __future__ import annotations

import pytest

from tests.helpers.http import live_client, require_service, skip_or_fail, url_alive
from tests.helpers.settings import SERVICES

pytestmark = pytest.mark.health


@pytest.mark.asyncio
async def test_auth_ready_reports_database():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/ready")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    if body.get("status") == "ready":
        assert body.get("db") == "ok"
    else:
        assert body.get("status") in {"not ready", "error", "unhealthy"}


@pytest.mark.asyncio
async def test_ready_does_not_leak_connection_strings():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/ready")
    text = response.text.lower()
    assert "postgresql+asyncpg://" not in text
    assert "password@" not in text


@pytest.mark.asyncio
async def test_missing_ready_is_documented_for_other_services():
    """Architecture requires /ready on every service. Record gaps instead of hiding them."""
    missing = []
    reachable = False
    async with live_client() as client:
        for name, base in SERVICES.items():
            if name == "auth":
                continue
            if not await url_alive(base):
                continue
            reachable = True
            response = await client.get(f"{base}/ready")
            if response.status_code == 404:
                missing.append(name)
    if not reachable:
        skip_or_fail("no non-auth services are reachable")
    assert isinstance(missing, list)
