from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.db import get_db, engine, Base
# Import models to ensure they are registered with Base
from app import models
from app.api import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    from app.services.github import github_service
    await github_service.close()

app = FastAPI(
    title="DeployHub Auth Service",
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
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/ready")
async def ready(db = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception:
        # Never echo driver/connection details -- that leaks internal topology.
        return {"status": "not ready", "error": "database unavailable"}

# We will include routers here
app.include_router(auth.router, prefix="/auth")
