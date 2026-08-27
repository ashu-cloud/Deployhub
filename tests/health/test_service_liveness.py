from __future__ import annotations

import pytest

from tests.helpers.http import live_client, require_service, skip_or_fail, url_alive
from tests.helpers.settings import SERVICES

pytestmark = pytest.mark.health


@pytest.mark.parametrize("name", list(SERVICES))
@pytest.mark.asyncio
async def test_service_health_returns_ok(name: str):
    base = await require_service(name)
    async with live_client() as client:
        response = await client.get(f"{base}/health")
    assert response.status_code == 200, f"{name} /health returned {response.status_code}: {response.text}"
    body = response.json()
    assert body.get("status") in {"ok", "healthy", "ready"}
    assert "traceback" not in response.text.lower()
    assert "password" not in response.text.lower()
    assert "secret" not in response.text.lower()


@pytest.mark.asyncio
async def test_health_is_fast():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/health")
    assert response.elapsed.total_seconds() < 2.0


@pytest.mark.asyncio
async def test_health_does_not_require_auth():
    """Liveness probes must stay unauthenticated so orchestrators can hit them."""
    reachable = []
    async with live_client() as client:
        for name, base in SERVICES.items():
            if await url_alive(base):
                reachable.append(name)
                response = await client.get(f"{base}/health")
                assert response.status_code == 200
                assert "www-authenticate" not in {k.lower() for k in response.headers}
    if not reachable:
        skip_or_fail("no microservices are reachable")


@pytest.mark.asyncio
async def test_unknown_path_is_not_500():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/definitely-not-a-route-xyz")
    assert response.status_code in {404, 405}
    assert response.status_code < 500
