from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.db import engine, Base
from app.core.kafka import kafka_client
# Import models to ensure they are registered with Base
from app import models
from app.api import projects, env_vars, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Start Kafka Producer
    await kafka_client.start()
    
    yield
    
    # 3. Shutdown gracefully
    await kafka_client.stop()

app = FastAPI(title="DeployHub Project Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(env_vars.router, prefix="/projects", tags=["env_vars"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
