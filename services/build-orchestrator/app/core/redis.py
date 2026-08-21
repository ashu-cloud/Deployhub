import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class BuildLock:
    def __init__(self, project_id: str):
        self.lock = redis_client.lock(
            f"build:lock:{project_id}",
            timeout=settings.BUILD_TIMEOUT_SECONDS,
            blocking_timeout=5,
        )

    async def __aenter__(self):
        if not await self.lock.acquire():
            raise Exception("A build is already in progress for this project")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.lock.release()
        except redis.exceptions.LockError:
            pass # Lock might have expired
