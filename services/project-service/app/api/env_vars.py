from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Project, EnvironmentVariable
from app.schemas.project import EnvVarCreate, EnvVarResponse
from app.services.encryption import encryption_service

router = APIRouter()

async def verify_project_access(project_id: UUID, user_id: str, db: AsyncSession):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/{project_id}/env-vars", response_model=EnvVarResponse, status_code=status.HTTP_201_CREATED)
async def create_env_var(
    project_id: UUID,
    env_in: EnvVarCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_project_access(project_id, user_id, db)
    
    # Encrypt value before saving
    encrypted_value = encryption_service.encrypt(env_in.value)

    # Check if key already exists, update if it does
    result = await db.execute(select(EnvironmentVariable).where(
        EnvironmentVariable.project_id == project_id,
        EnvironmentVariable.key == env_in.key
    ))
    existing = result.scalars().first()
    
    if existing:
        existing.encrypted_value = encrypted_value
        await db.commit()
        await db.refresh(existing)
        return existing
        
    new_var = EnvironmentVariable(
        project_id=project_id,
        key=env_in.key,
        encrypted_value=encrypted_value
    )
    db.add(new_var)
    await db.commit()
    await db.refresh(new_var)
    
    return new_var

@router.get("/{project_id}/env-vars", response_model=List[EnvVarResponse])
async def list_env_vars(
    project_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await verify_project_access(project_id, user_id, db)
    
    result = await db.execute(select(EnvironmentVariable).where(EnvironmentVariable.project_id == project_id))
    return result.scalars().all()
