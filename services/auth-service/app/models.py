import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    github_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    expires_at = Column(DateTime(timezone=True))
