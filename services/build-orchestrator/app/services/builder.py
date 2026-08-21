import os
import shutil
import asyncio
import logging
from sqlalchemy.future import select

from app.core.db import AsyncSessionLocal
from app.core.redis import BuildLock
from app.core.kafka import kafka_client
from app.models import Deployment
from app.services.docker_runner import docker_runner
from app.services.log_streamer import log_streamer
from app.schemas.events import BuildCompletedEvent, BuildFailedEvent

logger = logging.getLogger(__name__)

class BuilderService:
    async def process_build(self, payload: dict):
        deployment_id = payload.get("deployment_id")
        project_id = payload.get("project_id")
        repo_url = payload.get("repo_url")
        branch = payload.get("git_branch")
        
        if not all([deployment_id, project_id, repo_url]):
            logger.error(f"Invalid payload missing required fields: {payload}")
            return
            
        logger.info(f"Starting build orchestration for deployment {deployment_id}")
        
        # 1. Acquire Distributed Lock
        try:
            async with BuildLock(project_id):
                # 2. Update status to 'building'
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
                    deployment = result.scalars().first()
                    if deployment and deployment.status == 'queued':
                        deployment.status = 'building'
                        await db.commit()
                
                # 3. Clone repository
                work_dir = f"/tmp/builds/{deployment_id}"
                os.makedirs(work_dir, exist_ok=True)
                
                logger.info(f"Cloning {repo_url} branch {branch} to {work_dir}")
                # For real app, use GitHub API token in URL: https://x-access-token:{token}@github.com/...
                # In this MVP, we use subprocess to clone public repos
                process = await asyncio.create_subprocess_shell(
                    f"git clone --depth 1 -b {branch} {repo_url} {work_dir}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Git clone failed: {stderr.decode()}")
                
                # 4. Fetch Env Vars
                # In a real app, query Project Service or DB for encrypted env vars, decrypt them here.
                # env_vars = [f"{k}={v}" for k, v in decrypted_vars.items()]
                env_vars = ["NODE_ENV=production"]
                
                # 5. Run Docker Build & Stream Logs
                container = await docker_runner.run_build_container(work_dir, env_vars)
                
                # Stream logs concurrently while waiting for container
                stream_task = asyncio.create_task(log_streamer.stream_logs(container, deployment_id))
                exit_code = await docker_runner.wait_and_cleanup(container)
                await stream_task
                
                if exit_code != 0:
                    raise Exception(f"Build container exited with code {exit_code}")
                
                # 6. Publish Success
                logger.info(f"Build successful for {deployment_id}")
                event = BuildCompletedEvent(
                    deployment_id=deployment_id,
                    project_id=project_id,
                    s3_path=f"deployments/{project_id}/{deployment_id}" # Mock S3 path
                )
                await kafka_client.send_event("build.completed", event.model_dump(mode="json"), key=project_id)
                
                # Cleanup workspace
                shutil.rmtree(work_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Build failed for {deployment_id}: {e}")
            # Publish Failure
            fail_event = BuildFailedEvent(
                deployment_id=deployment_id,
                project_id=project_id,
                error=str(e)
            )
            await kafka_client.send_event("build.failed", fail_event.model_dump(mode="json"), key=project_id)
            
            # Update status in DB
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
                deployment = result.scalars().first()
                if deployment:
                    deployment.status = 'failed'
                    await db.commit()

builder_service = BuilderService()
