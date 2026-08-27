from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import Any


def exceptions_of(results: Iterable[Any]) -> list[BaseException]:
    return [item for item in results if isinstance(item, BaseException)]


def statuses_of(results: Iterable[Any]) -> list[int]:
    codes = []
    for item in results:
        if isinstance(item, BaseException):
            continue
        codes.append(item.status_code)
    return codes


async def bound_gather(jobs: list, *, limit: int = 25) -> list:
    semaphore = asyncio.Semaphore(limit)

    async def run(job):
        async with semaphore:
            return await job

    return await asyncio.gather(*[run(job) for job in jobs], return_exceptions=True)
