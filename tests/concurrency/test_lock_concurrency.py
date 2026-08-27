from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from tests.helpers.http import skip_or_fail, tcp_open
from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.concurrency


@pytest.mark.asyncio
async def test_build_lock_allows_only_one_holder():
    if not tcp_open("127.0.0.1", 6379):
        skip_or_fail("redis is not reachable at 127.0.0.1:6379")

    project_id = str(uuid4())
    held = asyncio.Event()
    release = asyncio.Event()
    outcomes: list[str] = []

    with service_on_path("build-orchestrator"):
        from app.core.redis import BuildLock

        async def winner():
            try:
                async with BuildLock(project_id):
                    outcomes.append("acquired")
                    held.set()
                    await release.wait()
            except Exception as exc:
                outcomes.append(f"winner-error:{exc}")

        async def loser():
            await held.wait()
            try:
                async with BuildLock(project_id):
                    outcomes.append("second-acquired")
            except Exception:
                outcomes.append("contended")
            finally:
                release.set()

        await asyncio.gather(winner(), loser())
        from app.core.redis import redis_client

        await redis_client.aclose()

    assert "acquired" in outcomes
    assert "second-acquired" not in outcomes
    assert "contended" in outcomes


@pytest.mark.asyncio
async def test_build_lock_serializes_overlapping_critical_sections():
    if not tcp_open("127.0.0.1", 6379):
        skip_or_fail("redis is not reachable at 127.0.0.1:6379")

    project_id = str(uuid4())
    current = 0
    max_overlap = 0
    lock = asyncio.Lock()

    with service_on_path("build-orchestrator"):
        from app.core.redis import BuildLock

        async def worker():
            nonlocal current, max_overlap
            try:
                async with BuildLock(project_id):
                    async with lock:
                        current += 1
                        max_overlap = max(max_overlap, current)
                    await asyncio.sleep(0.05)
                    async with lock:
                        current -= 1
            except Exception:
                return

        await asyncio.gather(*[worker() for _ in range(3)])
        from app.core.redis import redis_client

        await redis_client.aclose()

    assert max_overlap <= 1, f"build lock allowed {max_overlap} overlapping holders"
