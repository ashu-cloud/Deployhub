import logging
import os
import shutil
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.future import select

from app.core.db import engine, Base, AsyncSessionLocal
from app.core.kafka import kafka_client
from app.services.s3_uploader import s3_uploader
from app.models import Deployment
from app.schemas.events import DeploymentUploadedEvent
# Import models to ensure they are registered with Base
from app import models

logger = logging.getLogger(__name__)


def _artifact_dir(local_build_dir: str) -> str:
    for name in ("out", "dist", "build"):
        candidate = os.path.join(local_build_dir, name)
        if os.path.isdir(candidate) and os.listdir(candidate):
            return candidate
    return local_build_dir


async def process_build_completed(payload: dict):
    deployment_id = payload.get("deployment_id")
    project_id = payload.get("project_id")
    
    logger.info(f"Processing upload for deployment {deployment_id}")
    
    try:
        local_build_dir = f"/tmp/builds/{deployment_id}"
        s3_prefix = f"deployments/{project_id}/{deployment_id}"
        
        # 1. Update status to 'uploading'
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'uploading'
                await db.commit()
                
        # 2. Upload to S3 (MinIO) from the shared builds volume.
        if os.path.isdir(local_build_dir):
            await s3_uploader.upload_directory(_artifact_dir(local_build_dir), s3_prefix)
        else:
            logger.error(
                f"Build dir {local_build_dir} not found on the shared volume; "
                "upload-service and build-orchestrator must mount the same builds volume."
            )
            raise FileNotFoundError(local_build_dir)
            
        # 3. Update status to 'uploaded' and set s3_path
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'uploaded'
                deployment.s3_path = s3_prefix
                await db.commit()
                
        # 4. Publish deployment.uploaded event
        event = DeploymentUploadedEvent(
            deployment_id=deployment_id,
            project_id=project_id,
            s3_path=s3_prefix
        )
        await kafka_client.send_event("deployment.uploaded", event.model_dump(mode="json"), key=project_id)
        logger.info(f"Published deployment.uploaded for {deployment_id}")
        shutil.rmtree(local_build_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Upload failed for deployment {deployment_id}: {e}")
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
                deployment = result.scalars().first()
                if deployment:
                    deployment.status = 'failed'
                    await db.commit()
            
            # Inform the rest of the system
            event = {"deployment_id": deployment_id, "project_id": project_id, "error": str(e)}
            await kafka_client.send_event("build.failed", event, key=project_id)
            
            # Inform the frontend via Redis PubSub
            import json
            from app.core.redis import redis_client
            await redis_client.publish(
                f"deployment:{deployment_id}:status",
                json.dumps({"status": "failed", "error": f"Upload failed: {str(e)}"})
            )
        except Exception as recovery_err:
            logger.error(f"Failed to run recovery path for {deployment_id}: {recovery_err}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Ensure S3 Bucket exists
    await s3_uploader.init_bucket()
    
    # Start Kafka Producer & Consumer
    await kafka_client.start(message_handler=process_build_completed)
    
    yield
    
    await kafka_client.stop()

app = FastAPI(title="DeployHub Upload Service", lifespan=lifespan)

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
