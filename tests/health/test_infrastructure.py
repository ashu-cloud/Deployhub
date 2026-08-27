from __future__ import annotations

import pytest

from tests.helpers.http import live_client, skip_or_fail, tcp_open
from tests.helpers.settings import INFRA

pytestmark = pytest.mark.health


def test_postgres_accepts_tcp():
    host, port = INFRA["postgres_host"], INFRA["postgres_port"]
    if not tcp_open(host, port):
        skip_or_fail(f"postgres is not reachable at {host}:{port}")


def test_redis_accepts_tcp():
    if not tcp_open("127.0.0.1", 6379):
        skip_or_fail("redis is not reachable at 127.0.0.1:6379")


def test_kafka_accepts_tcp():
    host, port = INFRA["kafka_host"], INFRA["kafka_port"]
    if not tcp_open(host, port):
        skip_or_fail(f"kafka is not reachable at {host}:{port}")


@pytest.mark.asyncio
async def test_redis_ping():
    pytest.importorskip("redis")
    import redis.asyncio as redis

    if not tcp_open("127.0.0.1", 6379):
        skip_or_fail("redis is not reachable")
    client = redis.from_url(INFRA["redis_url"], decode_responses=True)
    try:
        assert await client.ping() is True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_minio_liveness():
    url = INFRA["minio_url"]
    async with live_client() as client:
        try:
            response = await client.get(f"{url}/minio/health/live")
        except Exception as exc:
            skip_or_fail(f"minio is not reachable: {exc}")
    assert response.status_code in {200, 204}


@pytest.mark.asyncio
async def test_caddy_responds_on_http():
    url = INFRA["caddy_http"]
    async with live_client() as client:
        try:
            response = await client.get(url)
        except Exception as exc:
            skip_or_fail(f"caddy is not reachable: {exc}")
    assert response.status_code in {200, 404}
    assert response.status_code < 500


@pytest.mark.asyncio
async def test_caddy_admin_api_config():
    url = INFRA["caddy_admin"]
    async with live_client() as client:
        try:
            response = await client.get(f"{url}/config/")
        except Exception as exc:
            skip_or_fail(f"caddy admin is not reachable: {exc}")
    assert response.status_code in {200, 401, 403}
