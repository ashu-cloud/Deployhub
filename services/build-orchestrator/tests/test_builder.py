import pytest
import uuid
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# We must mock db and docker before importing builder
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.builder import builder_service
from app.schemas.events import BuildCompletedEvent, BuildFailedEvent

@pytest.fixture
def mock_payload():
    return {
        "deployment_id": str(uuid.uuid4()),
        "project_id": str(uuid.uuid4()),
        "git_commit": "abc1234",
        "git_branch": "main",
        "repo_url": "https://github.com/user/repo"
    }

@pytest.mark.asyncio
@patch('app.services.builder.BuildLock')
@patch('app.services.builder.AsyncSessionLocal')
@patch('app.services.builder.asyncio.create_subprocess_shell')
@patch('app.services.builder.docker_runner')
@patch('app.services.builder.log_streamer')
@patch('app.services.builder.kafka_client')
async def test_process_build_success(
    mock_kafka, mock_log_streamer, mock_docker, mock_subprocess, mock_db, mock_lock, mock_payload
):
    # Setup mocks
    mock_kafka.send_event = AsyncMock()
    mock_lock.return_value.__aenter__.return_value = AsyncMock()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = MagicMock(status='queued')
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    mock_db.return_value.__aenter__.return_value = mock_session
    
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b'stdout', b'stderr')
    mock_proc.returncode = 0
    mock_subprocess.return_value = mock_proc
    
    mock_container = MagicMock()
    mock_docker.run_build_container = AsyncMock(return_value=mock_container)
    mock_docker.wait_and_cleanup = AsyncMock(return_value=0) # Exit code 0
    mock_log_streamer.stream_logs = AsyncMock()
    
    # Run
    await builder_service.process_build(mock_payload)
    
    # Assert Docker was run
    mock_docker.run_build_container.assert_called_once()
    mock_log_streamer.stream_logs.assert_called_once_with(mock_container, mock_payload['deployment_id'])
    
    # Assert Kafka published BuildCompletedEvent
    mock_kafka.send_event.assert_called_once()
    args, kwargs = mock_kafka.send_event.call_args
    assert args[0] == "build.completed"
    assert "s3_path" in args[1]
    assert kwargs["key"] == mock_payload["project_id"]

@pytest.mark.asyncio
@patch('app.services.builder.BuildLock')
@patch('app.services.builder.AsyncSessionLocal')
@patch('app.services.builder.asyncio.create_subprocess_shell')
@patch('app.services.builder.docker_runner')
@patch('app.services.builder.log_streamer')
@patch('app.services.builder.kafka_client')
async def test_process_build_docker_failure(
    mock_kafka, mock_log_streamer, mock_docker, mock_subprocess, mock_db, mock_lock, mock_payload
):
    mock_kafka.send_event = AsyncMock()
    mock_lock.return_value.__aenter__.return_value = AsyncMock()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = MagicMock(status='queued')
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    mock_db.return_value.__aenter__.return_value = mock_session
    
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b'', b'')
    mock_proc.returncode = 0
    mock_subprocess.return_value = mock_proc
    
    mock_container = MagicMock()
    mock_docker.run_build_container = AsyncMock(return_value=mock_container)
    # Docker returns exit code 1
    mock_docker.wait_and_cleanup = AsyncMock(return_value=1)
    mock_log_streamer.stream_logs = AsyncMock() 
    
    # Run
    await builder_service.process_build(mock_payload)
    
    # Assert Kafka published BuildFailedEvent
    mock_kafka.send_event.assert_called_once()
    args, kwargs = mock_kafka.send_event.call_args
    assert args[0] == "build.failed"
    assert "exited with code 1" in args[1]["error"]

@pytest.mark.asyncio
@patch('app.services.builder.BuildLock')
@patch('app.services.builder.AsyncSessionLocal')
@patch('app.services.builder.kafka_client')
async def test_process_build_lock_failure(mock_kafka, mock_db, mock_lock, mock_payload):
    mock_kafka.send_event = AsyncMock()
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = MagicMock(status='queued')
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    mock_db.return_value.__aenter__.return_value = mock_session
    # Simulate another build has the lock (Lock raises exception)
    mock_lock.side_effect = Exception("A build is already in progress")
    
    await builder_service.process_build(mock_payload)
    
    # Should publish build.failed
    mock_kafka.send_event.assert_called_once()
    args, kwargs = mock_kafka.send_event.call_args
    assert args[0] == "build.failed"
    assert "A build is already in progress" in args[1]["error"]
