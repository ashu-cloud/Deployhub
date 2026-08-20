from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProjectCreate(BaseModel):
    repo_url: str
    repo_name: str

class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    repo_name: str
    repo_url: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class EnvVarCreate(BaseModel):
    key: str
    value: str

class EnvVarResponse(BaseModel):
    id: UUID
    key: str
    created_at: datetime
    # Value is intentionally omitted for security

    class Config:
        from_attributes = True
