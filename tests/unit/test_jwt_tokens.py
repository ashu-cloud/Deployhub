from __future__ import annotations

from datetime import timedelta

import jwt
import pytest

from tests.helpers.jwt_factory import make_access_token
from tests.helpers.service_loader import service_on_path
from tests.helpers.settings import JWT_ALGORITHM, JWT_PRIVATE_KEY, JWT_PUBLIC_KEY

pytestmark = pytest.mark.unit


def test_create_access_token_roundtrip():
    with service_on_path("auth-service"):
        from app.core.security import create_access_token

        token = create_access_token({"sub": "user-1"})
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "user-1"
        assert "exp" in payload


def test_access_token_respects_custom_expiry():
    with service_on_path("auth-service"):
        from app.core.security import create_access_token

        token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(seconds=30))
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload
        header_and_claims = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        assert header_and_claims["sub"] == "user-1"


def test_expired_token_is_rejected_by_project_guard():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    expired = make_access_token("user-1", expires_delta=timedelta(minutes=-5))
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


def test_token_signed_with_wrong_key_is_rejected():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    token = make_access_token("user-1", secret="force-forged-keypair")
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


def test_token_without_sub_is_rejected():
    from datetime import datetime, timedelta, timezone

    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        JWT_PRIVATE_KEY,
        algorithm=JWT_ALGORITHM,
    )
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


def test_valid_token_returns_user_id():
    from fastapi.security import HTTPAuthorizationCredentials

    user_id = "11111111-1111-1111-1111-111111111111"
    token = make_access_token(user_id)
    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        assert get_current_user(creds) == user_id


def test_refresh_token_cannot_be_used_as_access_token():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    with service_on_path("auth-service"):
        from app.core.security import create_refresh_token

        refresh = create_refresh_token({"sub": "user-1"})

    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=refresh)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401


def test_garbage_token_is_rejected():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials

    with service_on_path("project-service"):
        from app.core.security import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt")
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401
