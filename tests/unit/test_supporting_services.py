from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit


def test_ai_prompt_includes_error_and_log_tail():
    with service_on_path("build-orchestrator"):
        from app.services.ai_diagnoser import AiDiagnoser

        diagnoser = AiDiagnoser()
        lines = [f"log-{i}" for i in range(120)]
        prompt = diagnoser._build_prompt(lines, "Module not found")
        assert "Module not found" in prompt
        assert "log-119" in prompt
        assert "log-0" not in prompt
        assert "Root Cause" in prompt


@pytest.mark.asyncio
async def test_diagnose_noop_without_api_key():
    with service_on_path("build-orchestrator"):
        from app.services.ai_diagnoser import AiDiagnoser

        diagnoser = AiDiagnoser()
        diagnoser.groq_client = None
        await diagnoser.diagnose("dep-1", ["line"], "boom")


@pytest.mark.asyncio
async def test_log_streamer_publishes_decoded_lines():
    with service_on_path("build-orchestrator"):
        from app.services.log_streamer import LogStreamer

        class FakeContainer:
            async def log(self, **_kwargs):
                yield b"\x00\x00\x00\x00\x00\x00\x00\x00npm install\n"
                yield "build ok\n"

        streamer = LogStreamer()
        with patch("app.services.log_streamer.redis_client") as redis:
            redis.publish = AsyncMock()
            buffer = await streamer.stream_logs(FakeContainer(), "dep-1")
        assert any("npm install" in line or "build ok" in line for line in buffer)
        assert redis.publish.await_count >= 1


@pytest.mark.asyncio
async def test_caddy_manager_posts_route():
    with service_on_path("deployment-service"):
        from app.services.caddy_manager import CaddyManager

        mgr = CaddyManager()
        response = MagicMock()
        response.raise_for_status = MagicMock()
        mgr.client = MagicMock()
        mgr.client.post = AsyncMock(return_value=response)
        await mgr.add_route("demo", "deployments/p/d")
        mgr.client.post.assert_awaited()
        args, kwargs = mgr.client.post.await_args
        assert args[0].startswith("/config/")
        assert "demo" in str(kwargs["json"])


@pytest.mark.asyncio
async def test_upload_handler_skips_when_build_dir_missing():
    with service_on_path("upload-service"):
        from app.main import process_build_completed

        payload = {"deployment_id": str(__import__("uuid").uuid4()), "project_id": str(__import__("uuid").uuid4())}
        with (
            patch("app.main.AsyncSessionLocal") as db,
            patch("app.main.s3_uploader") as s3,
            patch("app.main.kafka_client") as kafka,
            patch("os.path.isdir", return_value=False),
        ):
            session = AsyncMock()
            result = MagicMock()
            scalars = MagicMock()
            dep = MagicMock()
            scalars.first.return_value = dep
            result.scalars.return_value = scalars
            session.execute.return_value = result
            db.return_value.__aenter__.return_value = session
            kafka.send_event = AsyncMock()
            s3.upload_directory = AsyncMock()
            await process_build_completed(payload)
            s3.upload_directory.assert_not_called()
            kafka.send_event.assert_not_called()
