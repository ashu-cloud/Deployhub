from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit


def _payload(**overrides):
    data = {
        "deployment_id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "git_commit": "abc1234",
        "git_branch": "main",
        "repo_url": "https://github.com/user/repo",
    }
    data.update(overrides)
    return data


@pytest.mark.asyncio
async def test_process_build_ignores_incomplete_payload():
    with service_on_path("build-orchestrator"):
        from app.services.builder import builder_service

        with patch("app.services.builder.kafka_client") as kafka:
            kafka.send_event = AsyncMock()
            await builder_service.process_build({"deployment_id": "x"})
            kafka.send_event.assert_not_called()


@pytest.mark.asyncio
async def test_process_build_success_publishes_completed():
    payload = _payload()
    with service_on_path("build-orchestrator"):
        from app.services.builder import builder_service

        with (
            patch("app.services.builder.BuildLock") as mock_lock,
            patch("app.services.builder.AsyncSessionLocal") as mock_db,
            patch("app.services.builder.asyncio.create_subprocess_exec") as mock_subprocess,
            patch("app.services.builder.docker_runner") as mock_docker,
            patch("app.services.builder.log_streamer") as mock_logs,
            patch("app.services.builder.kafka_client") as mock_kafka,
            patch("app.services.builder.os.makedirs"),
            patch.object(builder_service, "_load_project_env_vars", AsyncMock(return_value=["NODE_ENV=production"])),
        ):
            mock_kafka.send_event = AsyncMock()
            mock_lock.return_value.__aenter__.return_value = AsyncMock()
            mock_lock.return_value.__aexit__.return_value = False
            session = AsyncMock()
            result = MagicMock()
            scalars = MagicMock()
            scalars.first.return_value = MagicMock(status="queued")
            result.scalars.return_value = scalars
            session.execute.return_value = result
            mock_db.return_value.__aenter__.return_value = session

            proc = AsyncMock()
            proc.communicate.return_value = (b"ok", b"")
            proc.returncode = 0
            mock_subprocess.return_value = proc
            container = MagicMock()
            mock_docker.run_build_container = AsyncMock(return_value=container)
            mock_docker.wait_and_cleanup = AsyncMock(return_value=0)
            mock_logs.stream_logs = AsyncMock(return_value=["line"])

            await builder_service.process_build(payload)

            mock_docker.run_build_container.assert_awaited()
            args, kwargs = mock_kafka.send_event.await_args
            assert args[0] == "build.completed"
            assert kwargs["key"] == payload["project_id"]


@pytest.mark.asyncio
async def test_process_build_docker_failure_publishes_failed():
    payload = _payload()
    with service_on_path("build-orchestrator"):
        from app.services.builder import builder_service

        with (
            patch("app.services.builder.BuildLock") as mock_lock,
            patch("app.services.builder.AsyncSessionLocal") as mock_db,
            patch("app.services.builder.asyncio.create_subprocess_exec") as mock_subprocess,
            patch("app.services.builder.docker_runner") as mock_docker,
            patch("app.services.builder.log_streamer") as mock_logs,
            patch("app.services.builder.kafka_client") as mock_kafka,
            patch("app.services.builder.os.makedirs"),
            patch.object(builder_service, "_load_project_env_vars", AsyncMock(return_value=["NODE_ENV=production"])),
        ):
            mock_kafka.send_event = AsyncMock()
            mock_lock.return_value.__aenter__.return_value = AsyncMock()
            mock_lock.return_value.__aexit__.return_value = False
            session = AsyncMock()
            result = MagicMock()
            scalars = MagicMock()
            scalars.first.return_value = MagicMock(status="queued")
            result.scalars.return_value = scalars
            session.execute.return_value = result
            mock_db.return_value.__aenter__.return_value = session
            proc = AsyncMock()
            proc.communicate.return_value = (b"", b"")
            proc.returncode = 0
            mock_subprocess.return_value = proc
            mock_docker.run_build_container = AsyncMock(return_value=MagicMock())
            mock_docker.wait_and_cleanup = AsyncMock(return_value=1)
            mock_logs.stream_logs = AsyncMock(return_value=["error"])

            await builder_service.process_build(payload)
            args, _kwargs = mock_kafka.send_event.await_args
            assert args[0] == "build.failed"
            assert "exited with code 1" in args[1]["error"]


@pytest.mark.asyncio
async def test_process_build_lock_contention():
    payload = _payload()
    with service_on_path("build-orchestrator"):
        from app.services.builder import builder_service

        with (
            patch("app.services.builder.BuildLock") as mock_lock,
            patch("app.services.builder.AsyncSessionLocal") as mock_db,
            patch("app.services.builder.kafka_client") as mock_kafka,
        ):
            mock_kafka.send_event = AsyncMock()
            session = AsyncMock()
            result = MagicMock()
            scalars = MagicMock()
            scalars.first.return_value = MagicMock(status="queued")
            result.scalars.return_value = scalars
            session.execute.return_value = result
            mock_db.return_value.__aenter__.return_value = session
            mock_lock.side_effect = Exception("A build is already in progress")

            await builder_service.process_build(payload)
            args, _kwargs = mock_kafka.send_event.await_args
            assert args[0] == "build.failed"
            assert "already in progress" in args[1]["error"]


@pytest.mark.asyncio
async def test_git_clone_failure_marks_failed():
    payload = _payload()
    with service_on_path("build-orchestrator"):
        from app.services.builder import builder_service

        with (
            patch("app.services.builder.BuildLock") as mock_lock,
            patch("app.services.builder.AsyncSessionLocal") as mock_db,
            patch("app.services.builder.asyncio.create_subprocess_exec") as mock_subprocess,
            patch("app.services.builder.kafka_client") as mock_kafka,
            patch("app.services.builder.os.makedirs"),
        ):
            mock_kafka.send_event = AsyncMock()
            mock_lock.return_value.__aenter__.return_value = AsyncMock()
            mock_lock.return_value.__aexit__.return_value = False
            session = AsyncMock()
            result = MagicMock()
            scalars = MagicMock()
            scalars.first.return_value = MagicMock(status="queued")
            result.scalars.return_value = scalars
            session.execute.return_value = result
            mock_db.return_value.__aenter__.return_value = session
            proc = AsyncMock()
            proc.communicate.return_value = (b"", b"fatal: repository not found")
            proc.returncode = 128
            mock_subprocess.return_value = proc

            await builder_service.process_build(payload)
            args, _kwargs = mock_kafka.send_event.await_args
            assert args[0] == "build.failed"
            assert "Git clone failed" in args[1]["error"]
