from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


def make_project(
    *,
    user_id: str | None = None,
    repo_url: str = "https://github.com/acme/demo",
    repo_name: str = "demo",
    status: str = "active",
):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        user_id=user_id or uuid4(),
        repo_name=repo_name,
        repo_url=repo_url,
        github_webhook_id="hook-1",
        status=status,
        created_at=now,
    )


def make_env_var(*, key: str = "NODE_ENV", encrypted_value: str = "cipher"):
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        key=key,
        encrypted_value=encrypted_value,
        created_at=datetime.now(timezone.utc),
    )


def make_deployment(*, status: str = "queued", s3_path: str | None = "deployments/p/d"):
    return SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        git_commit="a" * 40,
        git_branch="main",
        status=status,
        s3_path=s3_path,
        deployment_number=1,
        deployed_at=datetime.now(timezone.utc) if status == "live" else None,
        created_at=datetime.now(timezone.utc),
        version=0,
    )


def mock_session(*, first=None, all_items=None, execute_side_effect=None) -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.first.return_value = first
    scalars.all.return_value = all_items if all_items is not None else ([] if first is None else [first])
    result.scalars.return_value = scalars
    if execute_side_effect is not None:
        session.execute.side_effect = execute_side_effect
    else:
        session.execute.return_value = result
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session
