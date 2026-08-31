from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import asyncio
import json
import logging

from app.core.db import get_db, AsyncSessionLocal
from app.core.redis import redis_client
from app.core.security import get_current_user, get_current_user_from_token
from app.models import Deployment, Project
from app.services.caddy_manager import caddy_manager, slugify_subdomain
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("/{project_id}")
async def get_deployments(project_id: UUID, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deployment).where(Deployment.project_id == project_id).order_by(Deployment.created_at.desc())
    )
    deployments = result.scalars().all()
    return deployments

@router.get("/detail/{deployment_id}")
async def get_deployment_detail(deployment_id: UUID, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

@router.post("/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: UUID, user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 1. Fetch deployment to rollback TO
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment or deployment.status != 'live':
        raise HTTPException(status_code=400, detail="Deployment not found or not live")

    # 2. Re-route Caddy using the same subdomain scheme as a live deploy
    proj_res = await db.execute(select(Project).where(Project.id == deployment.project_id))
    project = proj_res.scalars().first()
    subdomain = project.repo_name if project else f"project-{deployment.project_id}"
    await caddy_manager.add_route(subdomain, deployment.s3_path)

    live_url = f"http://{slugify_subdomain(subdomain)}.{settings.BASE_DOMAIN}"
    return {"message": "Rollback successful", "live_url": live_url}

@router.websocket("/ws/{deployment_id}")
async def websocket_deployment_logs(websocket: WebSocket, deployment_id: str, token: str | None = Query(default=None)):
    # Browsers cannot set custom headers on the WebSocket handshake, so the
    # access token travels as a query parameter and is validated the same
    # way get_current_user_from_token validates it for HTTP routes.
    try:
        get_current_user_from_token(token or "")
    except Exception:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    pubsub = redis_client.pubsub()
    channel = f"build:{deployment_id}:logs"
    status_channel = f"deployment:{deployment_id}:status"
    ai_diagnosis_channel = f"build:{deployment_id}:ai_diagnosis"
    
    await pubsub.subscribe(channel, status_channel, ai_diagnosis_channel)
    logger.info(f"WebSocket client connected to channels for {deployment_id}")

    try:
        # Initial greeting and handshake
        await websocket.send_json({
            "type": "system",
            "message": f"Connected to build stream for {deployment_id}"
        })

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data"):
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                try:
                    parsed = json.loads(data)
                    await websocket.send_json(parsed)
                except Exception:
                    await websocket.send_text(data)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {deployment_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {deployment_id}: {e}")
    finally:
        await pubsub.unsubscribe(channel, status_channel, ai_diagnosis_channel)
