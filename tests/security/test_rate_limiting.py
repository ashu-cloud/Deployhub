from __future__ import annotations

import time

import pytest

from tests.helpers.http import live_client, require_service
from tests.helpers.jwt_factory import auth_header, make_access_token

pytestmark = [pytest.mark.security, pytest.mark.security_audit]


@pytest.mark.asyncio
async def test_burst_of_creates_is_rate_limited():
    """Architecture specifies per-user gateway limits; the service itself should not be unbounded."""
    base = await require_service("project")
    headers = auth_header(make_access_token("11111111-1111-4111-8111-111111111111"))
    statuses = []
    async with live_client() as client:
        start = time.perf_counter()
        for i in range(40):
            response = await client.post(
                f"{base}/projects/",
                headers=headers,
                json={"repo_name": f"rl-{i}", "repo_url": f"https://github.com/rl/rl-{i}-{int(start)}"},
            )
            statuses.append(response.status_code)
    assert 429 in statuses, (
        "SECURITY FINDING: 40 rapid POSTs to /projects/ produced no 429 "
        f"(codes={sorted(set(statuses))}); rate limiting is not enforced at the service"
    )
