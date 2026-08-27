from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
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

app = FastAPI(
    title="DeployHub Project Service",
    lifespan=lifespan,
    docs_url="/docs" if settings.EXPOSE_API_DOCS else None,
    redoc_url="/redoc" if settings.EXPOSE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.EXPOSE_API_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(env_vars.router, prefix="/projects", tags=["env_vars"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
