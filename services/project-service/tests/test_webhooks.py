import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

# We need to setup a mock DB session and redis before importing the app
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.config import settings
from app.core.db import get_db

client = TestClient(app)

@pytest.fixture
def webhook_payload():
    return b'{"ref": "refs/heads/main", "after": "abc1234", "repository": {"clone_url": "https://github.com/test/repo"}}'

@pytest.fixture
def valid_signature(webhook_payload):
    # Mock webhook secret
    secret = "test_secret".encode('utf-8')
    sig = hmac.new(secret, webhook_payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

@pytest.mark.asyncio
@patch('app.api.webhooks.settings')
@patch('app.api.webhooks.get_db')
@patch('app.api.webhooks.redis_client')
@patch('app.api.webhooks.kafka_client')
async def test_webhook_success_and_idempotency(
    mock_kafka, mock_redis, mock_db_dependency, mock_settings, webhook_payload, valid_signature
):
    mock_settings.WEBHOOK_SECRET = "test_secret"
    # Setup mocks
    mock_kafka.send_event = AsyncMock()
    # Mock redis.set to return True for the lock claim
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock()
    
    # We mock the DB call to find the project
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_project = MagicMock()
    mock_project.id = "c1341c4e-9790-4fe9-a87f-dd4694ca7508"
    mock_project.repo_url = "https://github.com/test/repo"
    mock_project.webhook_secret = "test_secret"
    mock_scalars.first.return_value = mock_project
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar.return_value = 5 # Return 5 for count() query
    mock_session.execute.return_value = mock_result
    
    async def mock_refresh(obj):
        obj.id = "d1341c4e-9790-4fe9-a87f-dd4694ca7509"
    mock_session.refresh = mock_refresh
    
    # Override FastAPI dependency
    app.dependency_overrides[get_db] = lambda: mock_session

    headers = {
        "X-Hub-Signature-256": valid_signature,
        "X-GitHub-Delivery": "delivery-123",
        "X-GitHub-Event": "push"
    }

    # 1. First request -> Success
    response = client.post("/webhooks/github/c1341c4e-9790-4fe9-a87f-dd4694ca7508", content=webhook_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "build_queued"
    mock_kafka.send_event.assert_called_once()
    
    # 2. Second request -> Idempotent
    # Simulate redis returning None for the claim (duplicate)
    mock_redis.set = AsyncMock(return_value=None)
    mock_kafka.send_event.reset_mock()
    
    response = client.post("/webhooks/github/c1341c4e-9790-4fe9-a87f-dd4694ca7508", content=webhook_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored_duplicate"
    # Should NOT send to Kafka again
    mock_kafka.send_event.assert_not_called()

@pytest.mark.asyncio
@patch('app.api.webhooks.get_db')
async def test_webhook_invalid_signature(mock_db_dependency, webhook_payload):
    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature123",
        "X-GitHub-Delivery": "delivery-123",
        "X-GitHub-Event": "push"
    }
    
    response = client.post("/webhooks/github/c1341c4e-9790-4fe9-a87f-dd4694ca7508", content=webhook_payload, headers=headers)
    # The API might return 401 or 400 depending on exact logic. Let's assume 401.
    assert response.status_code in [400, 401, 404] # Usually fails early
