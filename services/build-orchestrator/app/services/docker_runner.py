import aiodocker
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class DockerRunner:
    def __init__(self):
        self._docker = None

    @property
    def docker(self):
        if self._docker is None:
            self._docker = aiodocker.Docker()
        return self._docker

    async def close(self):
        if self._docker:
            await self._docker.close()

    async def run_build_container(self, project_dir: str, env_vars: list):
        """Runs the build inside an isolated container and returns the container instance for streaming"""
        deployment_id = project_dir.rstrip("/").split("/")[-1]
        if settings.BUILD_VOLUME_NAME:
            # Sibling containers started via the host docker.sock cannot see
            # this service's filesystem -- bind the shared named volume.
            binds = [f"{settings.BUILD_VOLUME_NAME}:/tmp/builds"]
            working_dir = f"/tmp/builds/{deployment_id}"
        else:
            binds = [f"{project_dir}:/app"]
            working_dir = "/app"

        config = {
            "Image": "node:20-alpine",
            "Cmd": ["sh", "-c", "if [ -f package-lock.json ]; then npm ci; else npm install; fi && npm run build"],
            "Env": env_vars,
            "HostConfig": {
                "Memory": 512 * 1024 * 1024, # 512MB limit
                "NanoCPUs": int(settings.BUILD_CPU_QUOTA * 1e9 / 100000), # ~1 CPU core
                "Binds": binds,
                "AutoRemove": False # We remove manually after streaming logs
            },
            "WorkingDir": working_dir,
            "Tty": False,
            "AttachStdout": True,
            "AttachStderr": True,
        }
        
        logger.info(f"Creating Docker container for {project_dir}")
        try:
            # Pull image if not exists (in production, we'd pre-pull or build our own images)
            # await self.docker.images.pull("node:20-alpine")
            
            container = await self.docker.containers.create_or_replace(config=config, name=f"build-{project_dir.split('/')[-1]}")
            await container.start()
            return container
        except Exception as e:
            logger.error(f"Failed to start Docker container: {e}")
            raise

    async def wait_and_cleanup(self, container):
        try:
            res = await container.wait(timeout=settings.BUILD_TIMEOUT_SECONDS)
            exit_code = res.get("StatusCode", 1)
            return exit_code
        finally:
            await container.delete(force=True)

docker_runner = DockerRunner()
