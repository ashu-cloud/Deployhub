from __future__ import annotations

import asyncio
from collections import Counter
from uuid import uuid4

import httpx
import pytest

from tests.helpers.concurrency import exceptions_of, statuses_of
from tests.helpers.hmac_factory import github_headers, github_push_payload
from tests.helpers.http import skip_or_fail, url_alive
from tests.helpers.jwt_factory import auth_header, make_access_token
from tests.helpers.settings import HTTP_TIMEOUT, SERVICES

pytestmark = pytest.mark.concurrency

USER = "11111111-1111-4111-8111-111111111111"
PARALLEL = 16


@pytest.mark.asyncio
async def test_same_delivery_id_is_idempotent_under_parallel_push():
    """Replay of one GitHub delivery id must queue at most one build."""
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers_auth = auth_header(make_access_token(USER))
    name = f"hookrace-{uuid4().hex[:8]}"
    body = github_push_payload()
    delivery_id = str(uuid4())
    hook_headers = github_headers(body)
    hook_headers["X-GitHub-Delivery"] = delivery_id

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers_auth,
            json={"repo_name": name, "repo_url": f"https://github.com/hookrace/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.status_code} {created.text[:200]}")
        project_id = created.json()["id"]

        results = await asyncio.gather(
            *[
                client.post(f"{base}/webhooks/github/{project_id}", content=body, headers=hook_headers)
                for _ in range(PARALLEL)
            ],
            return_exceptions=True,
        )

    errors = exceptions_of(results)
    assert not errors, f"webhook replay race raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"webhook replay produced 5xx: {Counter(codes)}"

    queued = []
    ignored = 0
    for response in results:
        if isinstance(response, BaseException) or response.status_code != 200:
            continue
        status = response.json().get("status")
        if status == "build_queued":
            queued.append(response.json().get("deployment_id"))
        elif status == "ignored_duplicate":
            ignored += 1

    assert len(queued) <= 1, (
        f"CONCURRENCY FINDING: delivery {delivery_id} queued {len(queued)} builds "
        "(idempotency check is not atomic)"
    )
    if queued:
        assert len(set(queued)) == 1


@pytest.mark.asyncio
async def test_unique_deliveries_all_accepted_or_coherently_rejected():
    base = SERVICES["project"]
    if not await url_alive(base):
        skip_or_fail("project service is not reachable")

    headers_auth = auth_header(make_access_token(USER))
    name = f"hookuniq-{uuid4().hex[:8]}"

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:
        created = await client.post(
            f"{base}/projects/",
            headers=headers_auth,
            json={"repo_name": name, "repo_url": f"https://github.com/hookuniq/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.status_code} {created.text[:200]}")
        project_id = created.json()["id"]

        async def fire(i: int):
            body = github_push_payload(commit_sha=f"{i + 1:040x}"[:40])
            return await client.post(
                f"{base}/webhooks/github/{project_id}",
                content=body,
                headers=github_headers(body),
            )

        results = await asyncio.gather(*[fire(i) for i in range(PARALLEL)], return_exceptions=True)

    errors = exceptions_of(results)
    assert not errors, f"unique webhook storm raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"unique webhooks produced 5xx: {Counter(codes)}"


@pytest.mark.asyncio
async def test_webhook_and_manual_deploy_in_parallel():
    project_base = SERVICES["project"]
    if not await url_alive(project_base):
        skip_or_fail("project service is not reachable")

    headers_auth = auth_header(make_access_token(USER))
    name = f"mixed-{uuid4().hex[:8]}"
    body = github_push_payload()
    hook_headers = github_headers(body)

    async with httpx.AsyncClient(timeout=max(HTTP_TIMEOUT, 20)) as client:
        created = await client.post(
            f"{project_base}/projects/",
            headers=headers_auth,
            json={"repo_name": name, "repo_url": f"https://github.com/mixed/{name}"},
        )
        if created.status_code != 201:
            pytest.skip(f"could not create project: {created.status_code} {created.text[:200]}")
        project_id = created.json()["id"]

        results = await asyncio.gather(
            client.post(f"{project_base}/webhooks/github/{project_id}", content=body, headers=hook_headers),
            client.post(f"{project_base}/projects/{project_id}/deploy", headers=headers_auth),
            client.post(f"{project_base}/projects/{project_id}/deploy", headers=headers_auth),
            return_exceptions=True,
        )

    errors = exceptions_of(results)
    assert not errors, f"mixed trigger race raised {errors[0]!r}"
    codes = statuses_of(results)
    assert all(code < 500 for code in codes), f"mixed trigger produced 5xx: {Counter(codes)}"
