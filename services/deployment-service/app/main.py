import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.core.db import engine, Base, AsyncSessionLocal
from app.core.kafka import kafka_client
from app.core.redis import redis_client
from app.services.caddy_manager import caddy_manager
from app.models import Deployment, Project
from app.schemas.events import DeploymentLiveEvent
from app.api.deployments import router as deployments_router
from app.core.config import settings

logger = logging.getLogger(__name__)

async def process_kafka_event(topic: str, payload: dict):
    if topic == "deployment.uploaded":
        await _handle_deployment_uploaded(payload)
    elif topic == "build.failed":
        await _handle_build_failed(payload)
    elif topic == "domain.added":
        await _handle_domain_added(payload)
    elif topic == "domain.removed":
        await _handle_domain_removed(payload)

async def _handle_deployment_uploaded(payload: dict):
    deployment_id = payload.get("deployment_id")
    project_id = payload.get("project_id")
    s3_path = payload.get("s3_path")
    
    logger.info(f"Processing live deployment for {deployment_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get project to figure out subdomain
            proj_res = await db.execute(select(Project).where(Project.id == project_id))
            project = proj_res.scalars().first()
            subdomain = project.repo_name if project else f"project-{project_id}"

            # 1. Update Caddy Route
            await caddy_manager.add_route(subdomain, s3_path)
            
            # 2. Update status to 'live'
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'live'
                deployment.deployed_at = datetime.now(timezone.utc)
                await db.commit()

            # 3. Add Custom Domain Routes
            from app.models import CustomDomain
            domain_res = await db.execute(select(CustomDomain).where(CustomDomain.project_id == project_id, CustomDomain.verified == True))
            for custom_domain in domain_res.scalars().all():
                try:
                    await caddy_manager.add_custom_domain_route(custom_domain.domain, s3_path)
                except Exception as e:
                    logger.error(f"Failed to add custom domain route for {custom_domain.domain}: {e}")
                
        # 4. Publish deployment.live event
        live_url = f"http://{subdomain}.{settings.BASE_DOMAIN}"
        event = DeploymentLiveEvent(
            deployment_id=deployment_id,
            project_id=project_id,
            live_url=live_url
        )
        await kafka_client.send_event("deployment.live", event.model_dump(mode="json"), key=project_id)
        
        # 4. Push real-time status to Redis Pub/Sub (for WebSocket)
        import json
        await redis_client.publish(
            f"deployment:{deployment_id}:status", 
            json.dumps({"status": "live", "url": live_url})
        )
        logger.info(f"Deployment {deployment_id} is now LIVE at {live_url}")
        
    except Exception as e:
        logger.error(f"Failed to make deployment live {deployment_id}: {e}")

async def _handle_build_failed(payload: dict):
    deployment_id = payload.get("deployment_id")
    logger.info(f"Processing build.failed for {deployment_id}")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'failed'
                await db.commit()
        await redis_client.publish(
            f"deployment:{deployment_id}:status",
            json.dumps({"status": "failed", "error": "Build process failed"})
        )
    except Exception as e:
        logger.error(f"Error handling build.failed for {deployment_id}: {e}")

async def _handle_domain_added(payload: dict):
    project_id = payload.get("project_id")
    domain = payload.get("domain")
    logger.info(f"Adding custom domain route {domain} for project {project_id}")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Deployment).where(Deployment.project_id == project_id, Deployment.status == 'live')
            )
            live_deployment = result.scalars().first()
            if live_deployment and live_deployment.s3_path:
                await caddy_manager.add_custom_domain_route(domain, live_deployment.s3_path)
    except Exception as e:
        logger.error(f"Error adding custom domain route for {domain}: {e}")

async def _handle_domain_removed(payload: dict):
    domain = payload.get("domain")
    logger.info(f"Removing custom domain route {domain}")
    try:
        await caddy_manager.remove_custom_domain_route(domain)
    except Exception as e:
        logger.error(f"Error removing custom domain route for {domain}: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await kafka_client.start(
        topics=["deployment.uploaded", "build.failed", "domain.added", "domain.removed"],
        message_handler=process_kafka_event
    )
    yield
    await kafka_client.stop()

app = FastAPI(title="DeployHub Deployment Service", lifespan=lifespan)
app.include_router(deployments_router)

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
