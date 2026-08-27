from __future__ import annotations

import socket
from contextlib import asynccontextmanager

import httpx
import pytest

from tests.helpers.settings import HTTP_TIMEOUT, REQUIRE_LIVE, SERVICES


def tcp_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


async def url_alive(url: str, path: str = "/health") -> bool:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=False) as client:
            response = await client.get(url.rstrip("/") + path)
            return response.status_code < 500
    except httpx.HTTPError:
        return False


def skip_or_fail(reason: str) -> None:
    if REQUIRE_LIVE:
        pytest.fail(reason)
    pytest.skip(reason)


async def require_service(name: str) -> str:
    base = SERVICES[name]
    if not await url_alive(base):
        skip_or_fail(f"{name} service is not reachable at {base}")
    return base


@asynccontextmanager
async def live_client():
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=False) as client:
        yield client
