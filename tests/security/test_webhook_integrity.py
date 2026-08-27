from __future__ import annotations

from uuid import uuid4

import pytest

from tests.helpers.hmac_factory import github_headers, github_push_payload, sign_body
from tests.helpers.http import live_client, require_service
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.security


def test_hmac_does_not_use_plain_equality():
    from tests.helpers.paths import SERVICES_DIR

    source = (SERVICES_DIR / "project-service" / "app" / "api" / "webhooks.py").read_text(encoding="utf-8")
    assert "hmac.compare_digest" in source
    assert "expected_signature == signature" not in source.replace(" ", "")


def test_empty_and_wrong_hmac_rejected_in_process():
    from fastapi import HTTPException

    body = github_push_payload()
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        with pytest.raises(HTTPException):
            verify_github_signature(body, None)  # type: ignore[arg-type]
        with pytest.raises(HTTPException):
            verify_github_signature(body, sign_body(body, secret="other-secret"))


@pytest.mark.asyncio
async def test_get_webhook_is_not_allowed():
    base = await require_service("project")
    async with live_client() as client:
        response = await client.get(f"{base}/webhooks/github/{uuid4()}")
    assert response.status_code in {405, 404}


@pytest.mark.asyncio
async def test_signature_header_cannot_be_omitted_with_valid_looking_body():
    base = await require_service("project")
    body = github_push_payload()
    headers = github_headers(body)
    headers.pop("X-Hub-Signature-256")
    async with live_client() as client:
        response = await client.post(f"{base}/webhooks/github/{uuid4()}", content=body, headers=headers)
    assert response.status_code == 400
