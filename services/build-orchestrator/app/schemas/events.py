from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class BuildQueuedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    git_commit: str
    git_branch: str
    repo_url: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BuildCompletedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    s3_path: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BuildFailedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    error: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
