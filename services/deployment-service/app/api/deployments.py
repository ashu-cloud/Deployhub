from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.db import get_db
from app.models import Deployment
from app.services.caddy_manager import caddy_manager

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("/{project_id}")
async def get_deployments(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deployment).where(Deployment.project_id == project_id).order_by(Deployment.created_at.desc())
    )
    deployments = result.scalars().all()
    return deployments

@router.post("/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: UUID, db: AsyncSession = Depends(get_db)):
    # 1. Fetch deployment to rollback TO
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment or deployment.status != 'live':
        raise HTTPException(status_code=400, detail="Deployment not found or not live")

    # 2. Re-route Caddy
    # In a real app we'd fetch the Project to get its name for the subdomain
    # For now we'll just mock the subdomain
    subdomain = f"project-{deployment.project_id}" 
    await caddy_manager.add_route(subdomain, deployment.s3_path)
    
    return {"message": "Rollback successful", "live_url": f"http://{subdomain}.deployhub.dev"}
