from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from tests.helpers.hmac_factory import github_push_payload, sign_body
from tests.helpers.jwt_factory import make_access_token
from tests.helpers.service_loader import service_on_path
from tests.helpers.settings import JWT_ALGORITHM, JWT_PRIVATE_KEY, JWT_PUBLIC_KEY

pytestmark = [pytest.mark.concurrency, pytest.mark.unit]

WORKERS = 32


def test_encryption_roundtrip_is_safe_under_threads():
    with service_on_path("project-service"):
        from app.services.encryption import EncryptionService

        svc = EncryptionService()
        plaintexts = [f"secret-value-{i}" for i in range(WORKERS)]

        def work(text: str) -> str:
            return svc.decrypt(svc.encrypt(text))

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            recovered = list(pool.map(work, plaintexts))
        assert recovered == plaintexts


@pytest.mark.asyncio
async def test_encryption_roundtrip_is_safe_under_asyncio():
    with service_on_path("project-service"):
        from app.services.encryption import EncryptionService

        svc = EncryptionService()

        async def work(i: int) -> str:
            token = await asyncio.to_thread(svc.encrypt, f"async-{i}")
            return await asyncio.to_thread(svc.decrypt, token)

        recovered = await asyncio.gather(*[work(i) for i in range(WORKERS)])
    assert recovered == [f"async-{i}" for i in range(WORKERS)]


def test_jwt_validate_under_thread_pool():
    tokens = [make_access_token(f"user-{i}") for i in range(WORKERS)]
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        def work(token: str) -> str:
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            return get_current_user(creds)

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futs = [pool.submit(work, token) for token in tokens]
            subjects = [fut.result() for fut in as_completed(futs)]
    assert set(subjects) == {f"user-{i}" for i in range(WORKERS)}


def test_hmac_verify_under_thread_pool():
    bodies = [github_push_payload(commit_sha=f"{i:040d}") for i in range(WORKERS)]
    with service_on_path("project-service"):
        from app.api.webhooks import verify_github_signature

        def work(body: bytes) -> bool:
            verify_github_signature(body, sign_body(body))
            return True

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            assert all(pool.map(work, bodies))


def test_jwt_decode_does_not_mix_subjects():
    def roundtrip(i: int) -> tuple[int, str]:
        token = jwt.encode({"sub": str(i)}, JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        return i, payload["sub"]

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, sub in pool.map(lambda n: roundtrip(n), range(WORKERS)):
            assert sub == str(i)
