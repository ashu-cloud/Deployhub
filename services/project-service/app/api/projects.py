from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List
from uuid import UUID
import re

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.rate_limit import rate_limit_create_project
from app.models import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.github import github_webhook_service
import asyncio
import httpx

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate, 
    user_id: str = Depends(rate_limit_create_project),
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

@router.post("/{project_id}/deploy")
async def trigger_deployment(
    project_id: UUID,
    branch: str = "main",
    commit_sha: str = Query(..., min_length=4, max_length=40, description="Git commit SHA (7–40 hex chars) or 'HEAD' for latest"),
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models import Deployment
    from app.schemas.events import BuildQueuedEvent
    from app.core.kafka import kafka_client

    # Count existing deployments to compute deployment_number (fixes BROKEN-06)
    count_query = await db.execute(select(func.count(Deployment.id)).where(Deployment.project_id == project_id))
    count = count_query.scalar() or 0

    new_dep = Deployment(
        project_id=project_id,
        git_commit=commit_sha,
        git_branch=branch,
        status="queued",
        deployment_number=count + 1
    )
    db.add(new_dep)
    await db.commit()
    await db.refresh(new_dep)

    event = BuildQueuedEvent(
        deployment_id=new_dep.id,
        project_id=project_id,
        git_commit=commit_sha,
        git_branch=branch,
        repo_url=project.repo_url
    )
    await kafka_client.send_event(
        topic="build.queued",
        value=event.model_dump(mode="json"),
        key=str(project_id)
    )

    return {
        "id": str(new_dep.id),
        "project_id": str(project_id),
        "status": "queued",
        "deployment_number": new_dep.deployment_number,
        "git_commit": commit_sha,
        "git_branch": branch,
        "created_at": new_dep.created_at.isoformat() if new_dep.created_at else None
    }


# ==========================================
# CUSTOM DOMAINS API
# ==========================================

from app.schemas.project import CustomDomainCreate, CustomDomainResponse
from app.models import CustomDomain

async def _verify_txt_record(domain: str, expected_value: str) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "nslookup", "-q=TXT", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            output = stdout.decode("utf-8", errors="ignore")
            if expected_value in output:
                return True
    except Exception:
        pass
    return False

@router.post("/{project_id}/domains", response_model=CustomDomainResponse, status_code=status.HTTP_201_CREATED)
async def add_custom_domain(
    project_id: UUID,
    domain_in: CustomDomainCreate,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project exists and belongs to user
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if domain is already in use by any project
    domain_check = await db.execute(select(CustomDomain).where(CustomDomain.domain == domain_in.domain))
    if domain_check.scalars().first():
        raise HTTPException(status_code=400, detail="Domain is already attached to a project")

    # Verify domain ownership via TXT record
    expected_txt = f"deployhub-verification={project_id}"
    is_verified = await _verify_txt_record(domain_in.domain, expected_txt)
    
    if not is_verified:
        raise HTTPException(
            status_code=400, 
            detail=f"Domain verification failed. Please add a TXT record to {domain_in.domain} with value: {expected_txt}"
        )

    # Add domain
    new_domain = CustomDomain(
        project_id=project_id,
        domain=domain_in.domain,
        verified=True
    )
    db.add(new_domain)
    await db.commit()
    await db.refresh(new_domain)

    # Trigger deployment-service to add Caddy route if project has a live deployment
    # Using Kafka to broadcast the domain addition
    from app.core.kafka import kafka_client
    await kafka_client.send_event(
        topic="domain.added",
        value={"project_id": str(project_id), "domain": domain_in.domain},
        key=str(project_id)
    )
    
    return new_domain

@router.get("/{project_id}/domains", response_model=List[CustomDomainResponse])
async def list_custom_domains(
    project_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    domains = await db.execute(select(CustomDomain).where(CustomDomain.project_id == project_id))
    return domains.scalars().all()

@router.delete("/{project_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_domain(
    project_id: UUID,
    domain_id: UUID,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify project exists and belongs to user
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    domain = await db.execute(select(CustomDomain).where(CustomDomain.id == domain_id, CustomDomain.project_id == project_id))
    db_domain = domain.scalars().first()
    if not db_domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    await db.delete(db_domain)
    await db.commit()

    # Broadcast removal so deployment-service drops the route
    from app.core.kafka import kafka_client
    await kafka_client.send_event(
        topic="domain.removed",
        value={"project_id": str(project_id), "domain": db_domain.domain},
        key=str(project_id)
    )

