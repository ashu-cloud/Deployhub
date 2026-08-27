#!/usr/bin/env python3
"""Generate local-only secrets for DeployHub.

Creates an RS256 JWT keypair under ``secrets/jwt/`` and a root ``.env`` file
with random webhook/encryption secrets and local-dev database passwords.
Both ``secrets/`` and ``.env`` are gitignored -- nothing here is committed.

Run once before ``docker-compose up``:

    python scripts/generate_secrets.py

Safe to re-run: existing secrets are left untouched.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

REPO_ROOT = Path(__file__).resolve().parents[1]
KEY_DIR = REPO_ROOT / "secrets" / "jwt"
# Deliberately NOT named `.env` at the repo root: every service's own
# pydantic-settings config also does `env_file=".env"` resolved from the
# process CWD, so a root `.env` would leak unrelated keys (POSTGRES_PASSWORD,
# MINIO_ROOT_PASSWORD, ...) into every service and crash on `extra_forbidden`
# when running tests/services locally from the repo root. Compose is told
# about this file explicitly via `--env-file`.
ENV_FILE = REPO_ROOT / "secrets" / "compose.env"


def ensure_jwt_keypair() -> None:
    private_path = KEY_DIR / "private.pem"
    public_path = KEY_DIR / "public.pem"
    if private_path.exists() and public_path.exists():
        print(f"[skip] JWT keypair already present at {KEY_DIR}")
        return

    KEY_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    try:
        private_path.chmod(0o600)
    except OSError:
        pass  # best effort on platforms without POSIX permissions
    print(f"[ok] Generated RS256 JWT keypair -> {KEY_DIR}")


def _read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        return values
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def ensure_env_file() -> None:
    existing = _read_env_file()
    defaults = {
        "WEBHOOK_SECRET": secrets.token_hex(32),
        "ENV_VAR_ENCRYPTION_KEY": secrets.token_hex(32),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(18),
        "MINIO_ROOT_PASSWORD": secrets.token_urlsafe(18),
        "GITHUB_CLIENT_ID": "dummy_client_id",
        "GITHUB_CLIENT_SECRET": "dummy_client_secret",
        "GROQ_API_KEY": "",
    }

    changed = False
    for key, value in defaults.items():
        if key not in existing:
            existing[key] = value
            changed = True

    if changed or not ENV_FILE.exists():
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(f"{key}={value}" for key, value in existing.items())
        ENV_FILE.write_text(body + "\n", encoding="utf-8")
        print(f"[ok] Wrote missing secrets to {ENV_FILE}")
    else:
        print(f"[skip] {ENV_FILE} already has every required secret")


if __name__ == "__main__":
    ensure_jwt_keypair()
    ensure_env_file()
    print(
        "\nDone. secrets/ is gitignored -- never commit it.\n"
        f"Start the stack with:\n\n"
        f"    docker-compose --env-file {ENV_FILE.relative_to(REPO_ROOT)} up -d --build\n"
    )
