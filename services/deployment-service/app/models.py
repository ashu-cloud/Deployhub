import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean
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

class Project(Base):
    """Read-only mapping of the projects table owned by project-service.

    Columns must match project-service so ``create_all`` on a shared Postgres
    does not invent a conflicting schema (the previous ``name`` column caused
    startup IntegrityErrors and broken subdomain routing).
    """
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=False)
    github_webhook_id = Column(String(100))
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class CustomDomain(Base):
    __tablename__ = "custom_domains"
    id = Column(UUID(as_uuid=True), primary_key=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    verified = Column(Boolean, default=False)
    ssl_cert_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
