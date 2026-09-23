from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.future import select

from app.core.db import engine, Base, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.kafka import kafka_client
from app.services.builder import builder_service
from app.services.docker_runner import docker_runner
# Import models to ensure they are registered with Base
from app import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start Kafka Producer & Consumer
    await kafka_client.start(message_handler=builder_service.process_build)
    
    yield
    
    # Shutdown gracefully
    await kafka_client.stop()
    await docker_runner.close()

app = FastAPI(title="DeployHub Build Orchestrator", lifespan=lifespan)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/builds/active")
async def get_active_builds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Deployment).where(models.Deployment.status == 'building'))
    active = result.scalars().all()
    return [{"deployment_id": d.id, "project_id": d.project_id, "status": d.status} for d in active]
