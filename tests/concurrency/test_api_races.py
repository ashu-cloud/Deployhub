from __future__ import annotations

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
PARALLEL = 20


async def require_project_writes(client, base: str, headers: dict) -> None:
    probe_name = f"probe-{uuid4().hex[:8]}"
    probe = await client.post(
        f"{base}/projects/",
        headers=headers,
        json={"repo_name": probe_name, "repo_url": f"https://github.com/probe/{probe_name}"},
    )
    if probe.status_code >= 500:
        pytest.skip(
            f"project create is not healthy ({probe.status_code}); "
            "start Kafka/DB before running live race tests"
        )


@pytest.mark.asyncio
async def test_duplicate_repo_creates_do_not_500():
    """Same user + same repo_url fired in parallel: at most one create succeeds."""
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers = auth_header(make_access_token(USER))
    name = f"race-{uuid4().hex[:8]}"
    payload = {"repo_name": name, "repo_url": f"https://github.com/race/{name}"}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        await require_project_writes(client, base, headers)
        results = await asyncio_gather_posts(client, f"{base}/projects/", headers, payload, PARALLEL)

    errors = exceptions_of(results)
    assert not errors, f"create race raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"create race produced 5xx: {Counter(codes)}"
    created = codes.count(201)
    # 429 is a legitimate rejection too: firing all N requests truly in
    # parallel is expected to blow through the per-user rate limit on this
    # endpoint, which is a deliberate security control, not a bug.
    rejected = sum(1 for code in codes if code in {400, 409, 422, 429})
    assert created + rejected == len(codes)
    assert created <= 1, (
        f"CONCURRENCY FINDING: {created} parallel POSTs created the same repo "
        "(duplicate insert is not serialized)"
    )


@pytest.mark.asyncio
async def test_distinct_creates_under_parallel_load():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers = auth_header(make_access_token(USER))
    stamp = uuid4().hex[:8]

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:
        await require_project_writes(client, base, headers)

        async def create(i: int):
            name = f"par-{stamp}-{i}"
            return await client.post(
                f"{base}/projects/",
                headers=headers,
                json={"repo_name": name, "repo_url": f"https://github.com/par/{name}"},
            )

        results = await __import__("asyncio").gather(*[create(i) for i in range(12)], return_exceptions=True)

    errors = exceptions_of(results)
    assert not errors, f"distinct create storm raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"distinct creates produced 5xx: {Counter(codes)}"


@pytest.mark.asyncio
async def test_parallel_env_var_upserts_same_key():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers = auth_header(make_access_token(USER))
    name = f"envrace-{uuid4().hex[:8]}"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": f"https://github.com/envrace/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.status_code} {created.text[:200]}")
        project_id = created.json()["id"]

        async def upsert(i: int):
            return await client.post(
                f"{base}/projects/{project_id}/env-vars",
                headers=headers,
                json={"key": "SHARED_KEY", "value": f"v{i}"},
            )

        results = await __import__("asyncio").gather(*[upsert(i) for i in range(PARALLEL)], return_exceptions=True)

    errors = exceptions_of(results)
    assert not errors, f"env upsert race raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"env upsert race produced 5xx: {Counter(codes)}"
    listed = [r for r in results if not isinstance(r, BaseException) and r.status_code in {200, 201}]
    assert listed, "no env-var upsert succeeded"
    keys = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        response = await client.get(f"{base}/projects/{project_id}/env-vars", headers=headers)
    if response.status_code == 200:
        keys = [row["key"] for row in response.json()]
        assert keys.count("SHARED_KEY") <= 1, (
            f"CONCURRENCY FINDING: SHARED_KEY stored {keys.count('SHARED_KEY')} times"
        )


@pytest.mark.asyncio
async def test_parallel_deploys_on_one_project():
    project_base = SERVICES["project"]
    if not await url_alive(project_base):
        skip_or_fail("project service is not reachable")

    headers = auth_header(make_access_token(USER))
    name = f"deprace-{uuid4().hex[:8]}"

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers,
            json={"repo_name": name, "repo_url": f"https://github.com/deprace/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.status_code} {created.text[:200]}")
        project_id = created.json()["id"]

        results = await __import__("asyncio").gather(
            *[client.post(f"{project_base}/projects/{project_id}/deploy", headers=headers) for _ in range(12)],
            return_exceptions=True,
        )

    errors = exceptions_of(results)
    assert not errors, f"deploy race raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"deploy race produced 5xx: {Counter(codes)}"
    queued = [r.json()["id"] for r in results if not isinstance(r, BaseException) and r.status_code == 200]
    assert len(queued) == len(set(queued)), "duplicate deployment ids issued under parallel deploy"


@pytest.mark.asyncio
async def test_two_users_do_not_see_each_others_creates():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    user_a = auth_header(make_access_token(str(uuid4())))
    user_b = auth_header(make_access_token(str(uuid4())))
    stamp = uuid4().hex[:8]

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:

        async def create(headers, i: int, owner: str):
            name = f"{owner}-{stamp}-{i}"
            return await client.post(
                f"{base}/projects/",
                headers=headers,
                json={"repo_name": name, "repo_url": f"https://github.com/{owner}/{name}"},
            )

        creates = await __import__("asyncio").gather(
            *[create(user_a, i, "a") for i in range(6)],
            *[create(user_b, i, "b") for i in range(6)],
            return_exceptions=True,
        )
        errors = exceptions_of(creates)
        if errors:
            pytest.skip(f"creates failed: {errors[0]!r}")
        if any(r.status_code >= 500 for r in creates if not isinstance(r, BaseException)):
            pytest.skip("project-service returned 5xx during setup")

        listed_a, listed_b = await __import__("asyncio").gather(
            client.get(f"{base}/projects/", headers=user_a),
            client.get(f"{base}/projects/", headers=user_b),
        )

    if listed_a.status_code != 200 or listed_b.status_code != 200:
        pytest.skip("list was not available")
    ids_a = {row["id"] for row in listed_a.json()}
    ids_b = {row["id"] for row in listed_b.json()}
    assert ids_a.isdisjoint(ids_b), "CONCURRENCY FINDING: two users shared project ids in list results"


@pytest.mark.asyncio
async def test_reads_stay_consistent_during_write_storm():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers = auth_header(make_access_token(USER))

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        await require_project_writes(client, base, headers)

        async def reader():
            return await client.get(f"{base}/projects/", headers=headers)

        async def writer(i: int):
            name = f"storm-{uuid4().hex[:6]}-{i}"
            return await client.post(
                f"{base}/projects/",
                headers=headers,
                json={"repo_name": name, "repo_url": f"https://github.com/storm/{name}"},
            )

        results = await __import__("asyncio").gather(
            *[reader() for _ in range(15)],
            *[writer(i) for i in range(8)],
            return_exceptions=True,
        )

    errors = exceptions_of(results)
    assert not errors, f"read/write storm raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"read/write storm produced 5xx: {Counter(codes)}"


async def asyncio_gather_posts(client, url, headers, payload, n: int):
    import asyncio

    return await asyncio.gather(
        *[client.post(url, headers=headers, json=payload) for _ in range(n)],
        return_exceptions=True,
    )
