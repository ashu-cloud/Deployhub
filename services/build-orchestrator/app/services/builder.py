import os
import re
import asyncio
import logging
from sqlalchemy.future import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.redis import BuildLock
from app.core.kafka import kafka_client
from app.models import Deployment
from app.services.docker_runner import docker_runner
from app.services.log_streamer import log_streamer
from app.schemas.events import BuildCompletedEvent, BuildFailedEvent

logger = logging.getLogger(__name__)

_SAFE_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
_SAFE_REPO_URL_RE = re.compile(r"^(https|git)://[A-Za-z0-9._~%/:@-]+$")


class BuilderService:
    @staticmethod
    def _validate_clone_inputs(repo_url: str, branch: str) -> None:
        """Reject anything that could be interpreted as a git/CLI flag or path escape."""
        if not branch or branch.startswith("-") or not _SAFE_BRANCH_RE.match(branch):
            raise ValueError(f"Refusing to clone: unsafe branch name {branch!r}")
        if not repo_url or repo_url.startswith("-") or not _SAFE_REPO_URL_RE.match(repo_url):
            raise ValueError(f"Refusing to clone: unsafe repo_url {repo_url!r}")

    async def _load_project_env_vars(self, project_id: str) -> list[str]:
        env_vars = ["NODE_ENV=production"]
        hex_key = settings.ENV_VAR_ENCRYPTION_KEY
        if not hex_key:
            return env_vars
        try:
            from sqlalchemy import text
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            import base64

            key = bytes.fromhex(hex_key)
            if len(key) != 32:
                logger.warning("ENV_VAR_ENCRYPTION_KEY is not 32 bytes; skipping project env vars")
                return env_vars
            aesgcm = AESGCM(key)

            async with AsyncSessionLocal() as db:
                rows = (
                    await db.execute(
                        text(
                            "SELECT key, encrypted_value FROM environment_variables WHERE project_id = :pid"
                        ),
                        {"pid": project_id},
                    )
                ).all()

            for row in rows:
                try:
                    data = base64.b64decode(row.encrypted_value.encode("utf-8"))
                    value = aesgcm.decrypt(data[:12], data[12:], None).decode("utf-8")
                    env_vars.append(f"{row.key}={value}")
                except Exception as exc:
                    logger.warning(f"Skipping env var {row.key}: {exc}")
        except Exception as exc:
            logger.warning(f"Could not load project env vars: {exc}")
        return env_vars

    async def process_build(self, payload: dict):
        deployment_id = payload.get("deployment_id")
        project_id = payload.get("project_id")
        repo_url = payload.get("repo_url")
        branch = payload.get("git_branch") or "main"
        
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

                self._validate_clone_inputs(repo_url, branch)

                logger.info(f"Cloning {repo_url} branch {branch} to {work_dir}")
                # For real app, use GitHub API token in URL: https://x-access-token:{token}@github.com/...
                # In this MVP, we clone public repos. Arguments are passed as an
                # argv list (never through a shell) so a malicious repo_url/branch
                # cannot inject shell metacharacters or extra git flags.
                process = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth", "1", "-b", branch, "--", repo_url, work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Git clone failed: {stderr.decode()}")
                
                env_vars = await self._load_project_env_vars(project_id)
                
                # 5. Run Docker Build & Stream Logs
                container = await docker_runner.run_build_container(work_dir, env_vars)
                
                # Stream logs concurrently while waiting for container
                stream_task = asyncio.create_task(log_streamer.stream_logs(container, deployment_id))
                exit_code = await docker_runner.wait_and_cleanup(container)
                log_buffer = await stream_task
                
                if exit_code != 0:
                    # Stash log buffer for exception handler
                    self.current_log_buffer = log_buffer
                    raise Exception(f"Build container exited with code {exit_code}")
                
                # 6. Publish Success
                logger.info(f"Build successful for {deployment_id}")
                event = BuildCompletedEvent(
                    deployment_id=deployment_id,
                    project_id=project_id,
                    s3_path=f"deployments/{project_id}/{deployment_id}" # Mock S3 path
                )
                await kafka_client.send_event("build.completed", event.model_dump(mode="json"), key=project_id)
                
                # Workspace is left on the shared volume for upload-service;
                # that service deletes it after a successful upload.
                
        except Exception as e:
            logger.error(f"Build failed for {deployment_id}: {e}")
            
            # Trigger AI Diagnosis in the background
            log_buffer = getattr(self, "current_log_buffer", [])
            from app.services.ai_diagnoser import ai_diagnoser
            asyncio.create_task(
                ai_diagnoser.diagnose(str(deployment_id), log_buffer, str(e))
            )
                
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
