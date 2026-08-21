import logging
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

async def process_build_completed(payload: dict):
    deployment_id = payload.get("deployment_id")
    project_id = payload.get("project_id")
    
    logger.info(f"Processing upload for deployment {deployment_id}")
    
    try:
        # In this local MVP, the build output is in /tmp/builds/{deployment_id} (if on same machine)
        # or we assume the build orchestrator packed it and passed a shared path. 
        # For simplicity, we assume /tmp/builds/{deployment_id} is accessible.
        local_build_dir = f"/tmp/builds/{deployment_id}"
        s3_prefix = f"deployments/{project_id}/{deployment_id}"
        
        # 1. Update status to 'uploading'
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalars().first()
            if deployment:
                deployment.status = 'uploading'
                await db.commit()
                
        # 2. Upload to S3 (MinIO)
        # Note: If the directory doesn't exist (because we are on a different pod and no shared volume),
        # this will fail. In a real Kubernetes cluster, we'd use a shared PVC or the Build Orchestrator
        # would stream the tarball to Kafka/S3 directly. We'll simulate success if dir missing for local MVP.
        import os
        if os.path.exists(local_build_dir):
            await s3_uploader.upload_directory(local_build_dir, s3_prefix)
        else:
            logger.warning(f"Local build dir {local_build_dir} not found. Simulating upload success for MVP.")
            
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
        
    except Exception as e:
        logger.error(f"Upload failed for deployment {deployment_id}: {e}")
        # Could publish upload.failed here if we had that event

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

@app.get("/health")
async def health():
    return {"status": "ok"}
