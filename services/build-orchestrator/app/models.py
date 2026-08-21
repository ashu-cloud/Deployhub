import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base

# We only need the Deployment model here to update status
class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    git_commit = Column(String(40), nullable=False)
    git_branch = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False) # 'queued', 'building', 'uploading', 'live', 'failed'
    s3_path = Column(String(500))
    deployment_number = Column(Integer, nullable=False)
    deployed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    version = Column(Integer, nullable=False, default=0) # For optimistic locking
