from __future__ import annotations

import asyncio
from collections import Counter
from uuid import uuid4

import httpx
import pytest

from tests.helpers.concurrency import exceptions_of, statuses_of
from tests.helpers.http import skip_or_fail, url_alive
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.settings import HTTP_TIMEOUT, SERVICES

pytestmark = pytest.mark.concurrency

USER = "11111111-1111-4111-8111-111111111111"


@pytest.mark.asyncio
async def test_all_health_endpoints_under_burst():
    reachable = {name: base for name, base in SERVICES.items() if await url_alive(base)}
    if not reachable:
        skip_or_fail("no microservices are reachable")

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        jobs = [
            client.get(f"{base}/health")
            for base in reachable.values()
            for _ in range(20)
        ]
        results = await asyncio.gather(*jobs, return_exceptions=True)

    errors = exceptions_of(results)
    assert not errors, f"health burst raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code == 200 for code in codes), f"health burst codes={Counter(codes)}"


@pytest.mark.asyncio
async def test_deployment_reads_under_parallel_clients():
    deploy_base = SERVICES["deployment"]
    project_base = SERVICES["project"]
    if not await url_alive(deploy_base):
        skip_or_fail("deployment service is not reachable")

    project_id = str(uuid4())
    headers = auth_header(make_access_token(USER))

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        if await url_alive(project_base):
            name = f"read-{uuid4().hex[:8]}"
            created = await client.post(
                f"{project_base}/projects/",
                headers=headers,
                json={"repo_name": name, "repo_url": f"https://github.com/read/{name}"},
            )
            if created.status_code == 201:
                project_id = created.json()["id"]

        results = await asyncio.gather(
            *[client.get(f"{deploy_base}/deployments/{project_id}") for _ in range(25)],
            *[client.get(f"{deploy_base}/deployments/detail/{uuid4()}") for _ in range(10)],
            return_exceptions=True,
        )

    errors = exceptions_of(results)
    assert not errors, f"deployment read burst raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"deployment reads produced 5xx: {Counter(codes)}"


@pytest.mark.asyncio
async def test_interleaved_service_calls_do_not_deadlock():
    """Hit auth, project, and deployment at once to surface event-loop / pool stalls."""
    live = {name: base for name, base in SERVICES.items() if await url_alive(base)}
    if len(live) < 2:
        skip_or_fail("need at least two reachable services")

    headers = auth_header(make_access_token(USER))
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        jobs = []
        if "auth" in live:
            jobs.extend([client.get(f"{live['auth']}/health") for _ in range(10)])
            jobs.extend([client.get(f"{live['auth']}/auth/github") for _ in range(5)])
        if "project" in live:
            jobs.extend([client.get(f"{live['project']}/projects/", headers=headers) for _ in range(10)])
        if "deployment" in live:
            jobs.extend([client.get(f"{live['deployment']}/health") for _ in range(10)])
        results = await asyncio.gather(*jobs, return_exceptions=True)

    errors = exceptions_of(results)
    assert not errors, f"interleaved calls raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"interleaved calls produced 5xx: {Counter(codes)}"
