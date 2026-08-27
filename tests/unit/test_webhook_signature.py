from __future__ import annotations

import hmac

import pytest
from fastapi import HTTPException

from tests.helpers.hmac_factory import github_push_payload, sign_body
from tests.helpers.service_loader import service_on_path
from tests.helpers.settings import WEBHOOK_SECRET

pytestmark = pytest.mark.unit


def test_valid_signature_is_accepted():
    body = github_push_payload()
    signature = sign_body(body)
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        verify_github_signature(body, signature)


def test_missing_signature_is_rejected():
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        with pytest.raises(HTTPException) as exc:
            verify_github_signature(b"{}", "")
        assert exc.value.status_code == 400
        assert "Missing signature" in exc.value.detail


def test_wrong_signature_is_rejected():
    body = github_push_payload()
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        with pytest.raises(HTTPException) as exc:
            verify_github_signature(body, "sha256=" + ("ab" * 32))
        assert exc.value.status_code == 400
        assert "Invalid signature" in exc.value.detail


def test_signature_for_different_body_is_rejected():
    body = github_push_payload()
    other = github_push_payload(commit_sha="b" * 40)
    signature = sign_body(other)
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        with pytest.raises(HTTPException):
            verify_github_signature(body, signature)


def test_compare_digest_is_used_for_hmac():
    """Guard against a future switch to `==` which is not timing-safe."""
    from tests.helpers.paths import SERVICES_DIR

    source = (SERVICES_DIR / "project-service" / "app" / "api" / "webhooks.py").read_text(encoding="utf-8")
    assert "hmac.compare_digest" in source
    assert WEBHOOK_SECRET
    # sanity: stdlib compare_digest agrees with our fixture
    body = b'{"ok":true}'
    left = sign_body(body)
    right = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, "sha256").hexdigest()
    assert hmac.compare_digest(left, right)
