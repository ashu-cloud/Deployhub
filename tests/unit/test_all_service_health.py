from __future__ import annotations

import httpx
import pytest

from tests.helpers.asgi import asgi_transport
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit

SERVICES = (
    "auth-service",
    "project-service",
    "build-orchestrator",
    "upload-service",
    "deployment-service",
)


@pytest.mark.parametrize("service", SERVICES)
@pytest.mark.asyncio
async def test_each_service_health_endpoint(service: str):
    try:
        with service_on_path(service):
            from app.main import app

            transport = asgi_transport(app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
    except ImportError as exc:
        pytest.skip(f"{service} dependencies missing: {exc}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
