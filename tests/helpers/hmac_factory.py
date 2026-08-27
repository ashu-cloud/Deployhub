from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

from tests.helpers.settings import WEBHOOK_SECRET


def sign_body(body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    digest = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def github_push_payload(
    *,
    commit_sha: str | None = None,
    branch: str = "main",
    clone_url: str = "https://github.com/test/repo",
) -> bytes:
    payload = {
        "ref": f"refs/heads/{branch}",
        "after": commit_sha or "a" * 40,
        "repository": {"clone_url": clone_url, "full_name": "test/repo"},
    }
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def github_headers(body: bytes, *, secret: str = WEBHOOK_SECRET, event: str = "push") -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sign_body(body, secret),
        "X-GitHub-Delivery": str(uuid4()),
        "X-GitHub-Event": event,
    }
