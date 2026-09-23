import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    git_commit = Column(String(40), nullable=False)
    git_branch = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    s3_path = Column(String(500))
    deployment_number = Column(Integer, nullable=False)
    deployed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    version = Column(Integer, nullable=False, default=0)
