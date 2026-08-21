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
    timestamp: datetime = datetime.utcnow()

class BuildCompletedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    s3_path: str
    timestamp: datetime = datetime.utcnow()

class BuildFailedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    error: str
    timestamp: datetime = datetime.utcnow()
