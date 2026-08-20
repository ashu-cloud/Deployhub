from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID
import re

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.github import github_webhook_service

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate, 
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Parse owner and repo from URL (e.g., https://github.com/owner/repo)
    match = re.search(r"github\.com/([^/]+)/([^/]+)", project_in.repo_url)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    
    owner, repo = match.groups()
    repo = repo.replace(".git", "")

    # Check if project exists
    result = await db.execute(select(Project).where(Project.repo_url == project_in.repo_url, Project.user_id == user_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Project already exists for this repository")

    # Create project in DB
    new_project = Project(
        user_id=user_id,
        repo_name=project_in.repo_name,
        repo_url=project_in.repo_url,
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    # Register webhook
    webhook_id = await github_webhook_service.register_webhook(owner, repo, str(new_project.id))
    
    new_project.github_webhook_id = webhook_id
    await db.commit()
    await db.refresh(new_project)

    return new_project

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.user_id == user_id, Project.status == 'active'))
    return result.scalars().all()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete
    project.status = 'archived'
    await db.commit()
