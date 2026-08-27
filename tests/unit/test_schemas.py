from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from tests.helpers.service_loader import service_on_path

pytestmark = pytest.mark.unit


def test_build_queued_event_requires_core_fields():
    with service_on_path("project-service"):
        from app.schemas.events import BuildQueuedEvent

        with pytest.raises(Exception):
            BuildQueuedEvent(deployment_id=uuid4(), project_id=uuid4())


def test_build_queued_event_accepts_valid_payload():
    with service_on_path("project-service"):
        from app.schemas.events import BuildQueuedEvent

        event = BuildQueuedEvent(
            deployment_id=uuid4(),
            project_id=uuid4(),
            git_commit="a" * 40,
            git_branch="main",
            repo_url="https://github.com/acme/demo",
        )
        dumped = event.model_dump(mode="json")
        assert dumped["git_branch"] == "main"
        assert "deployment_id" in dumped


def test_build_completed_and_failed_events():
    with service_on_path("build-orchestrator"):
        from app.schemas.events import BuildCompletedEvent, BuildFailedEvent

        done = BuildCompletedEvent(
            deployment_id=uuid4(),
            project_id=uuid4(),
            s3_path="deployments/p/d",
        )
        failed = BuildFailedEvent(
            deployment_id=uuid4(),
            project_id=uuid4(),
            error="clone failed",
        )
        assert done.s3_path.startswith("deployments/")
        assert "clone" in failed.error
        assert isinstance(done.timestamp, datetime)


def test_project_create_schema():
    with service_on_path("project-service"):
        from app.schemas.project import ProjectCreate

        model = ProjectCreate(repo_url="https://github.com/acme/demo", repo_name="demo")
        assert model.repo_name == "demo"
        with pytest.raises(Exception):
            ProjectCreate(repo_url="https://github.com/acme/demo")


def test_deployment_live_event():
    with service_on_path("deployment-service"):
        from app.schemas.events import DeploymentLiveEvent

        event = DeploymentLiveEvent(
            deployment_id=uuid4(),
            project_id=uuid4(),
            live_url="http://demo.deployhub.dev",
        )
        assert event.live_url.startswith("http://")


def test_upload_events():
    with service_on_path("upload-service"):
        from app.schemas.events import DeploymentUploadedEvent

        event = DeploymentUploadedEvent(
            deployment_id=uuid4(),
            project_id=uuid4(),
            s3_path="deployments/p/d",
        )
        dumped = event.model_dump(mode="json")
        assert dumped["s3_path"] == "deployments/p/d"
