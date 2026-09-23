from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProjectCreate(BaseModel):
    repo_url: str = Field(..., min_length=1, max_length=500)
    repo_name: str = Field(..., min_length=1, max_length=255)

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
    key: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., max_length=65536)

class EnvVarResponse(BaseModel):
    id: UUID
    key: str
    created_at: datetime
    # Value is intentionally omitted for security

    class Config:
        from_attributes = True

class CustomDomainCreate(BaseModel):
    # Matches a valid hostname or FQDN (e.g. sub.domain.com)
    domain: str = Field(..., min_length=3, max_length=255, pattern=r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")

class CustomDomainResponse(BaseModel):
    id: UUID
    project_id: UUID
    domain: str
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
