from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import asyncio
import json
import logging

from app.core.db import get_db, AsyncSessionLocal
from app.core.redis import redis_client
from app.models import Deployment
from app.services.caddy_manager import caddy_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("/{project_id}")
async def get_deployments(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deployment).where(Deployment.project_id == project_id).order_by(Deployment.created_at.desc())
    )
    deployments = result.scalars().all()
    return deployments

@router.get("/detail/{deployment_id}")
async def get_deployment_detail(deployment_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment

@router.post("/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: UUID, db: AsyncSession = Depends(get_db)):
    # 1. Fetch deployment to rollback TO
    result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
    deployment = result.scalars().first()
    if not deployment or deployment.status != 'live':
        raise HTTPException(status_code=400, detail="Deployment not found or not live")

    # 2. Re-route Caddy
    subdomain = f"project-{deployment.project_id}" 
    await caddy_manager.add_route(subdomain, deployment.s3_path)
    
    return {"message": "Rollback successful", "live_url": f"http://{subdomain}.deployhub.dev"}

@router.websocket("/ws/{deployment_id}")
async def websocket_deployment_logs(websocket: WebSocket, deployment_id: str):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    channel = f"build:{deployment_id}:logs"
    status_channel = f"deployment:{deployment_id}:status"
    
    await pubsub.subscribe(channel, status_channel)
    logger.info(f"WebSocket client connected to {channel}")

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
        await pubsub.unsubscribe(channel, status_channel)

