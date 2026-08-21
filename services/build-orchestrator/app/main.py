from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.db import engine, Base
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

@app.get("/health")
async def health():
    return {"status": "ok"}
