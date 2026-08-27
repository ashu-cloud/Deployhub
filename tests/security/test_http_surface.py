from __future__ import annotations

import pytest

from tests.helpers.http import live_client, require_service, skip_or_fail, url_alive
from tests.helpers.paths import SERVICES_DIR
from tests.helpers.settings import SERVICES

pytestmark = pytest.mark.security


@pytest.mark.security_audit
def test_cors_star_with_credentials_is_not_configured():
    source = (SERVICES_DIR / "auth-service" / "app" / "main.py").read_text(encoding="utf-8")
    wildcard = 'allow_origins=["*"]' in source.replace(" ", "") or "allow_origins=['*']" in source.replace(
        " ", ""
    )
    credentials = "allow_credentials=True" in source
    if wildcard and credentials:
        pytest.fail(
            "SECURITY FINDING: Auth CORS allows origin * together with allow_credentials=True"
        )


@pytest.mark.security_audit
@pytest.mark.asyncio
async def test_security_headers_on_json_apis():
    base = await require_service("auth")
    async with live_client() as client:
        response = await client.get(f"{base}/health")
    headers = {k.lower(): v for k, v in response.headers.items()}
    missing = [
        name
        for name in ("x-content-type-options", "x-frame-options", "referrer-policy")
        if name not in headers
    ]
    assert not missing, f"SECURITY FINDING: missing security headers on /health: {missing}"


@pytest.mark.security_audit
@pytest.mark.asyncio
async def test_openapi_docs_not_public_in_production_shape():
    base = await require_service("auth")
    async with live_client() as client:
        docs = await client.get(f"{base}/docs")
        openapi = await client.get(f"{base}/openapi.json")
    assert docs.status_code in {401, 403, 404}, (
        "SECURITY FINDING: FastAPI /docs is publicly reachable"
    )
    assert openapi.status_code in {401, 403, 404}, (
        "SECURITY FINDING: /openapi.json is publicly reachable"
    )


@pytest.mark.security_audit
def test_auth_callback_cookie_flags():
    """Cookie flags are asserted from source so we do not need a live GitHub code."""
    source = (SERVICES_DIR / "auth-service" / "app" / "api" / "auth.py").read_text(encoding="utf-8")
    assert "httponly=True" in source.replace(" ", "") or "httponly=True" in source
    assert "secure=True" in source
    assert "samesite" in source.lower()
    # Architecture calls for SameSite=Strict; lax is weaker for a refresh-style cookie.
    if 'samesite="lax"' in source.lower() or "samesite='lax'" in source.lower():
        pytest.fail("SECURITY FINDING: access_token cookie uses SameSite=Lax (architecture specifies Strict)")


@pytest.mark.asyncio
async def test_options_preflight_does_not_500():
    if not await url_alive(SERVICES["project"]):
        skip_or_fail("project service is not reachable")
    async with live_client() as client:
        response = await client.options(
            f"{SERVICES['project']}/projects/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert response.status_code < 500
