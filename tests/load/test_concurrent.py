from __future__ import annotations

import asyncio
from collections import Counter

import httpx
import pytest

from tests.helpers.hmac_factory import github_headers, github_push_payload
from tests.helpers.http import skip_or_fail, url_alive
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.settings import HTTP_TIMEOUT, SERVICES

pytestmark = [pytest.mark.load, pytest.mark.concurrency]

CONCURRENCY = 40


@pytest.mark.asyncio
async def test_parallel_health_checks_stay_healthy():
    reachable = [base for base in SERVICES.values() if await url_alive(base)]
    if not reachable:
        skip_or_fail("no microservices are reachable")

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:

        async def ping(url: str):
            response = await client.get(f"{url}/health")
            return url, response.status_code, response.elapsed.total_seconds()

        jobs = [ping(url) for url in reachable for _ in range(CONCURRENCY)]
        results = await asyncio.gather(*jobs, return_exceptions=True)

    failures = [r for r in results if isinstance(r, Exception) or r[1] != 200]
    latencies = [r[2] for r in results if not isinstance(r, Exception)]
    assert not failures, f"{len(failures)} health checks failed out of {len(results)}"
    p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
    assert p95 < 2.0, f"health p95 {p95:.3f}s exceeded 2s"


@pytest.mark.asyncio
async def test_parallel_unauth_list_is_consistently_denied():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        responses = await asyncio.gather(
            *[client.get(f"{base}/projects/") for _ in range(CONCURRENCY)]
        )
    codes = Counter(r.status_code for r in responses)
    assert set(codes) <= {401, 403}, f"unauth flood produced unexpected codes: {codes}"


@pytest.mark.asyncio
async def test_parallel_authenticated_lists():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")
    headers = auth_header(make_access_token("11111111-1111-4111-8111-111111111111"))
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        responses = await asyncio.gather(
            *[client.get(f"{base}/projects/", headers=headers) for _ in range(CONCURRENCY)]
        )
    failures = [r for r in responses if r.status_code >= 500]
    assert not failures, f"{len(failures)} of {len(responses)} list calls returned 5xx"
    assert all(r.status_code in {200, 401, 403} for r in responses)


@pytest.mark.asyncio
async def test_parallel_signed_webhooks_do_not_500():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")
    body = github_push_payload()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:

        async def fire():
            headers = github_headers(body)
            return await client.post(
                f"{base}/webhooks/github/00000000-0000-4000-8000-000000000099",
                content=body,
                headers=headers,
            )

        responses = await asyncio.gather(*[fire() for _ in range(CONCURRENCY)])
    assert all(r.status_code < 500 for r in responses)
    # unknown project -> 404; invalid/missing redis still must not 500
    assert {r.status_code for r in responses} <= {200, 400, 404}
