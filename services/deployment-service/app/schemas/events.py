from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class DeploymentLiveEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    live_url: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
