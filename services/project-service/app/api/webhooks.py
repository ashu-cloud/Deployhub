from fastapi import APIRouter, Request, HTTPException, Depends
import hmac
import hashlib
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.config import settings
from app.core.db import get_db
from app.core.redis import redis_client
from app.core.kafka import kafka_client
from app.models import Project, Deployment
from app.schemas.events import BuildQueuedEvent

router = APIRouter()

def verify_github_signature(payload: bytes, signature: str):
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
        
    mac = hmac.new(settings.WEBHOOK_SECRET.encode('utf-8'), msg=payload, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

@router.post("/github/{project_id}")
async def receive_webhook(
    project_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    event_type = request.headers.get("x-github-event")
    delivery_id = request.headers.get("x-github-delivery")
    
    # 1. Validate HMAC
    verify_github_signature(payload, signature)
    
    # We only care about push events
    if event_type != "push":
        return {"status": "ignored", "reason": "not a push event"}
        
    # Idempotency check using X-GitHub-Delivery. A plain GET-then-SETEX at the
    # end of the handler is a check-then-act race: under a parallel replay,
    # every request observes a cache miss and all of them queue a build. A
    # single atomic `SET NX` claims the delivery id up front -- only the
    # request that wins the claim proceeds, everyone else is a duplicate.
    cache_key = f"webhook:delivery:{delivery_id}" if delivery_id else None
    if cache_key:
        claimed = await redis_client.set(cache_key, "1", nx=True, ex=86400)
        if not claimed:
            return {"status": "ignored_duplicate"}

    try:
        data = json.loads(payload)

        # 2. Get project from DB
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalars().first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Extract commit info
        commit_sha = data.get("after")
        ref = data.get("ref", "")
        branch = ref.replace("refs/heads/", "")

        if not commit_sha or commit_sha == "0000000000000000000000000000000000000000":
            return {"status": "ignored", "reason": "branch deletion"}

        # Calculate deployment number using COUNT (fixes BROKEN-04 and BROKEN-06)
        count_query = await db.execute(
            select(func.count(Deployment.id)).where(Deployment.project_id == project_id)
        )
        count = count_query.scalar() or 0

        # 3. Create Deployment record
        deployment = Deployment(
            project_id=project_id,
            git_commit=commit_sha,
            git_branch=branch,
            status="queued",
            deployment_number=count + 1
        )
        db.add(deployment)
        await db.commit()
        await db.refresh(deployment)

        # 4. Publish to Kafka
        event = BuildQueuedEvent(
            deployment_id=deployment.id,
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
    except Exception:
        # Release the claim so a legitimate GitHub retry after a transient
        # failure (DB hiccup, Kafka unavailable, ...) is not permanently
        # treated as a duplicate.
        if cache_key:
            await redis_client.delete(cache_key)
        raise

    # Return 200 immediately
    return {"status": "build_queued", "deployment_id": str(deployment.id)}
