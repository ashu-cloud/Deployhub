import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False) # References users.id in Auth Service
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=False)
    github_webhook_id = Column(String(100))
    status = Column(String(50), default='active')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class EnvironmentVariable(Base):
    __tablename__ = "environment_variables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    key = Column(String(255), nullable=False)
    encrypted_value = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    verified = Column(Boolean, default=False)
    ssl_cert_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    git_commit = Column(String(40), nullable=False)
    git_branch = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False) # 'queued', 'building', 'uploading', 'live', 'failed'
    s3_path = Column(String(500))
    deployment_number = Column(Integer, nullable=False)
    deployed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    version = Column(Integer, nullable=False, default=0) # For optimistic locking
