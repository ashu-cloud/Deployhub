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
