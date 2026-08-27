"""Runtime endpoints and shared secrets used by the test suite.

Override any value with the matching environment variable so CI and
docker-compose networks can point tests at different hosts.

JWT signing key: if the repo has real secrets generated (via
``python scripts/generate_secrets.py``, mounted into the live docker-compose
stack), we reuse that exact keypair so tokens minted here validate against
the *live* auth/project/deployment services too. Otherwise we generate a
throwaway keypair once per test session -- good enough for in-process unit
tests that import service code directly and never talk to a real container.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from tests.helpers.paths import REPO_ROOT

SERVICES = {
    "auth": os.getenv("AUTH_URL", "http://127.0.0.1:8001"),
    "project": os.getenv("PROJECT_URL", "http://127.0.0.1:8002"),
    "build": os.getenv("BUILD_URL", "http://127.0.0.1:8004"),
    "upload": os.getenv("UPLOAD_URL", "http://127.0.0.1:8005"),
    "deployment": os.getenv("DEPLOYMENT_URL", "http://127.0.0.1:8006"),
}

INFRA = {
    "postgres_host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
    "postgres_user": os.getenv("POSTGRES_USER", "deployhub"),
    "postgres_password": os.getenv("POSTGRES_PASSWORD", "password"),
    "postgres_db": os.getenv("POSTGRES_DB", "deployhub"),
    "redis_url": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
    "kafka_host": os.getenv("KAFKA_HOST", "127.0.0.1"),
    "kafka_port": int(os.getenv("KAFKA_PORT", "19092")),
    "minio_url": os.getenv("MINIO_URL", "http://127.0.0.1:9000"),
    "caddy_http": os.getenv("CADDY_HTTP_URL", "http://127.0.0.1:80"),
    "caddy_admin": os.getenv("CADDY_ADMIN_URL", "http://127.0.0.1:2019"),
}

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")


def _generate_rsa_keypair(private_path: Path, public_path: Path) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_path.parent.mkdir(parents=True, exist_ok=True)
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


_REAL_KEY_DIR = REPO_ROOT / "secrets" / "jwt"
_FALLBACK_KEY_DIR = Path(tempfile.gettempdir()) / "deployhub_test_jwt_keys"

if (_REAL_KEY_DIR / "private.pem").is_file() and (_REAL_KEY_DIR / "public.pem").is_file():
    _KEY_DIR = _REAL_KEY_DIR
else:
    _KEY_DIR = _FALLBACK_KEY_DIR
    if not (_KEY_DIR / "private.pem").is_file() or not (_KEY_DIR / "public.pem").is_file():
        _generate_rsa_keypair(_KEY_DIR / "private.pem", _KEY_DIR / "public.pem")

JWT_PRIVATE_KEY_PATH = _KEY_DIR / "private.pem"
JWT_PUBLIC_KEY_PATH = _KEY_DIR / "public.pem"
JWT_PRIVATE_KEY = JWT_PRIVATE_KEY_PATH.read_text()
JWT_PUBLIC_KEY = JWT_PUBLIC_KEY_PATH.read_text()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

# Services imported in-process (via service_on_path) must resolve the same
# key files -- force these so a stray pre-set env var can't point them
# somewhere else mid-session.
os.environ["JWT_ALGORITHM"] = JWT_ALGORITHM
os.environ["JWT_PRIVATE_KEY_PATH"] = str(JWT_PRIVATE_KEY_PATH)
os.environ["JWT_PUBLIC_KEY_PATH"] = str(JWT_PUBLIC_KEY_PATH)


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


_dotenv = _read_dotenv(REPO_ROOT / "secrets" / "compose.env")

# Reuse the same shared secrets the live stack was started with, when present,
# so signed webhooks/tokens from this process validate against live services.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or _dotenv.get("WEBHOOK_SECRET") or "test-only-webhook-shared-secret"
os.environ.setdefault("WEBHOOK_SECRET", WEBHOOK_SECRET)

ENV_VAR_ENCRYPTION_KEY = (
    os.getenv("ENV_VAR_ENCRYPTION_KEY") or _dotenv.get("ENV_VAR_ENCRYPTION_KEY") or ("11" * 32)
)
os.environ.setdefault("ENV_VAR_ENCRYPTION_KEY", ENV_VAR_ENCRYPTION_KEY)

REQUIRE_LIVE = os.getenv("REQUIRE_LIVE", "").lower() in {"1", "true", "yes"}
HTTP_TIMEOUT = float(os.getenv("TEST_HTTP_TIMEOUT", "8"))
