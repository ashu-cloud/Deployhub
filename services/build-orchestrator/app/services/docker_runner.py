import aiodocker
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Minimal set of capabilities required for a Node.js npm build.
# All others are dropped. See `man 7 capabilities` for the full list.
_BUILD_CAP_DROP = [
    "ALL",          # Drop everything first …
]
_BUILD_CAP_ADD = [
    # … then re-grant only what npm/node genuinely needs:
    # (none — node:20-alpine builds successfully with zero extra caps)
]


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
        """Runs the build inside a hardened, isolated container and returns
        the container instance for log streaming.

        Security controls applied:
        - CapDrop=ALL  — no Linux capabilities (npm build needs none)
        - no-new-privileges — child processes cannot gain extra privileges
        - PidsLimit — caps fork-bomb potential
        - Memory + CPU limits — prevents resource exhaustion
        - NetworkMode=bridge by default; set BUILD_DISABLE_NETWORK=true in
          env to cut network entirely (for fully offline / pre-cached builds)
        """
        deployment_id = project_dir.rstrip("/").split("/")[-1]
        if settings.BUILD_VOLUME_NAME:
            # Sibling containers started via the host docker.sock cannot see
            # this service's filesystem -- bind the shared named volume.
            binds = [f"{settings.BUILD_VOLUME_NAME}:/tmp/builds"]
            working_dir = f"/tmp/builds/{deployment_id}"
        else:
            binds = [f"{project_dir}:/app"]
            working_dir = "/app"

        network_mode = "none" if settings.BUILD_DISABLE_NETWORK else "bridge"

        config = {
            "Image": "node:20-alpine",
            "Cmd": ["sh", "-c", "if [ -f package-lock.json ]; then npm ci; else npm install; fi && npm run build"],
            "Env": env_vars,
            "HostConfig": {
                "Memory": 512 * 1024 * 1024,              # 512 MB hard limit
                "MemorySwap": 512 * 1024 * 1024,          # disable swap (same as Memory)
                "NanoCPUs": int(settings.BUILD_CPU_QUOTA * 1e9 / 100000),
                "PidsLimit": 256,                          # block fork bombs
                "Binds": binds,
                "AutoRemove": False,                       # removed manually after log streaming
                "NetworkMode": network_mode,
                # Security hardening ─────────────────────────────────────────
                "CapDrop": _BUILD_CAP_DROP,                # drop ALL Linux capabilities
                "CapAdd": _BUILD_CAP_ADD,                  # add back none
                "SecurityOpt": ["no-new-privileges=true"], # child procs can't gain privs
                # ─────────────────────────────────────────────────────────────
            },
            "WorkingDir": working_dir,
            "Tty": False,
            "AttachStdout": True,
            "AttachStderr": True,
        }

        logger.info(f"Creating hardened Docker container for {project_dir} (network={network_mode})")
        try:
            container = await self.docker.containers.create_or_replace(
                config=config,
                name=f"build-{deployment_id}",
            )
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
