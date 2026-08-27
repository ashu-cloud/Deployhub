from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from tests.helpers.settings import JWT_ALGORITHM, JWT_PRIVATE_KEY

_forged_key_cache: str | None = None


def _forged_private_key() -> str:
    """A different, unrelated RSA key -- used to simulate a forged/wrong-key token."""
    global _forged_key_cache
    if _forged_key_cache is None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        _forged_key_cache = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()
    return _forged_key_cache


def make_access_token(
    user_id: str | None = None,
    *,
    secret: str | None = None,
    algorithm: str = JWT_ALGORITHM,
    expires_delta: timedelta | None = None,
    extra: dict | None = None,
) -> str:
    """Sign a test access token with the shared test/real RS256 keypair.

    Pass ``secret`` (any value; content is ignored) to instead sign with an
    unrelated keypair, simulating a forged token that real services must
    reject.
    """
    subject = user_id or str(uuid4())
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta is not None else timedelta(minutes=15))
    payload = {"sub": subject, "exp": expire, "iat": now, "type": "access"}
    if extra:
        payload.update(extra)
    signing_key = JWT_PRIVATE_KEY if secret is None else _forged_private_key()
    return jwt.encode(payload, signing_key, algorithm=algorithm)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
