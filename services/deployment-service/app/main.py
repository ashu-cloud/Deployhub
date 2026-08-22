import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.future import select
from datetime import datetime

from app.core.db import engine, Base, AsyncSessionLocal
from app.core.kafka import kafka_client
from app.core.redis import redis_client
from app.services.caddy_manager import caddy_manager
from app.models import Deployment, Project
from app.schemas.events import DeploymentLiveEvent
from app.api.deployments import router as deployments_router
from app.core.config import settings

logger = logging.getLogger(__name__)

async def process_deployment_uploaded(payload: dict):
    deployment_id = payload.get("deployment_id")
    project_id = payload.get("project_id")
    s3_path = payload.get("s3_path")
    
    logger.info(f"Processing live deployment for {deployment_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            # Get project to figure out subdomain
            proj_res = await db.execute(select(Project).where(Project.id == project_id))
            project = proj_res.scalars().first()
            subdomain = project.name if project else f"project-{project_id}"

            # 1. Update Caddy Route
            await caddy_manager.add_route(subdomain, s3_path)
            
            # 2. Update status to 'live'
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'live'
                deployment.deployed_at = datetime.utcnow()
                await db.commit()
                
        # 3. Publish deployment.live event
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await kafka_client.start(message_handler=process_deployment_uploaded)
    yield
    await kafka_client.stop()

app = FastAPI(title="DeployHub Deployment Service", lifespan=lifespan)
app.include_router(deployments_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
