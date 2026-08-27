from __future__ import annotations

import re

import pytest

from tests.helpers.http import live_client, require_service, url_alive
from tests.helpers.paths import COMPOSE_FILE, REPO_ROOT, SERVICES_DIR
from tests.helpers.settings import SERVICES

pytestmark = [pytest.mark.security, pytest.mark.security_audit]


def test_jwt_default_secret_is_not_a_placeholder():
    config = (SERVICES_DIR / "auth-service" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert "supersecretkey_change_in_production" not in config, (
        "SECURITY FINDING: JWT_SECRET_KEY default is a hardcoded placeholder shared across services"
    )


def test_webhook_secret_is_not_hardcoded():
    config = (SERVICES_DIR / "project-service" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    assert "supersecret_webhook_key_123" not in config, (
        "SECURITY FINDING: WEBHOOK_SECRET has a hardcoded default"
    )


def test_env_var_key_is_256_bit():
    config = (SERVICES_DIR / "project-service" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    match = re.search(r'ENV_VAR_ENCRYPTION_KEY:\s*str\s*=\s*"([0-9a-fA-F]+)"', config)
    if not match:
        # No hardcoded key material at all (e.g. default "") is the compliant
        # state -- the real key must come from the environment.
        return
    hex_key = match.group(1)
    assert len(hex_key) >= 64, (
        f"SECURITY FINDING: ENV_VAR_ENCRYPTION_KEY is {len(hex_key)//2} bytes "
        "(AES-256 requires 32 bytes / 64 hex chars)"
    )


def test_compose_does_not_inline_cloud_api_keys():
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    if "gsk_" in text:
        pytest.fail(
            "SECURITY FINDING: docker-compose.yml inlines a Groq-style API key; use ${GROQ_API_KEY} only"
        )
    if re.search(r"sk-[A-Za-z0-9]{20,}", text):
        pytest.fail("SECURITY FINDING: docker-compose.yml appears to inline a secret key")


def test_minio_and_postgres_defaults_are_not_in_compose_for_shared_use():
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    findings = []
    if "minioadmin123" in text:
        findings.append("MinIO root password is the well-known default minioadmin123")
    if "POSTGRES_PASSWORD: password" in text or "POSTGRES_PASSWORD: password" in text.replace('"', ""):
        findings.append("Postgres password is the literal 'password'")
    assert not findings, "SECURITY FINDING: " + "; ".join(findings)


def test_caddy_admin_is_not_bound_to_all_interfaces():
    caddy = (REPO_ROOT / "infra" / "caddy" / "Caddyfile").read_text(encoding="utf-8")
    assert "admin 0.0.0.0:2019" not in caddy, (
        "SECURITY FINDING: Caddy admin API is bound to 0.0.0.0:2019"
    )


def test_s3_bucket_public_grant_is_scoped_to_deployments_prefix():
    """DeployHub serves public static sites, so *some* public-read grant is
    the intended product behaviour (like any static host). The finding was
    that the grant covered the *entire* bucket -- including any future
    non-public prefix -- instead of just the `deployments/` output.
    """
    source = (SERVICES_DIR / "upload-service" / "app" / "services" / "s3_uploader.py").read_text(
        encoding="utf-8"
    )
    if '"Principal": "*"' not in source:
        return
    assert '/deployments/*"' in source or "/deployments/*'" in source, (
        "SECURITY FINDING: MinIO bucket policy grants s3:GetObject to Principal * "
        "over the whole bucket instead of just the deployments/ prefix"
    )
    assert re.search(r'Resource["\']?\s*:\s*\[f?"arn:aws:s3:::\{?[^}]*\}?/\*"\]', source) is None, (
        "SECURITY FINDING: bucket policy Resource is still the unscoped bucket wildcard */*"
    )


@pytest.mark.asyncio
async def test_health_and_ready_do_not_echo_exceptions():
    if not await url_alive(SERVICES["auth"]):
        pytest.skip("auth service is not reachable")
    async with live_client() as client:
        response = await client.get(f"{SERVICES['auth']}/ready")
    body = response.json()
    if "error" in body:
        err = str(body["error"]).lower()
        assert "traceback" not in err
        assert "postgresql+asyncpg://" not in err
        assert "password" not in err
        # Returning raw exception text is itself a finding if it looks like a driver error.
        if "asyncpg" in err or "sqlalchemy" in err or "connection refused" in err:
            pytest.fail("SECURITY FINDING: /ready leaks internal exception text")
