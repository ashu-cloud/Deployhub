from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class BuildCompletedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    s3_path: str
    timestamp: datetime = datetime.utcnow()

class DeploymentUploadedEvent(BaseModel):
    deployment_id: UUID
    project_id: UUID
    s3_path: str
    timestamp: datetime = datetime.utcnow()
