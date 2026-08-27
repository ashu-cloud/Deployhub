from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer()


class MissingJwtKeyError(RuntimeError):
    """Raised when the RS256 key material has not been provisioned."""


@lru_cache(maxsize=1)
def _load_private_key() -> str:
    path = Path(settings.JWT_PRIVATE_KEY_PATH)
    if not path.is_file():
        raise MissingJwtKeyError(
            f"JWT private key not found at {path}. Run "
            "`python scripts/generate_secrets.py` and mount secrets/jwt into this service."
        )
    return path.read_text()


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    path = Path(settings.JWT_PUBLIC_KEY_PATH)
    if not path.is_file():
        raise MissingJwtKeyError(
            f"JWT public key not found at {path}. Run "
            "`python scripts/generate_secrets.py` and mount secrets/jwt into this service."
        )
    return path.read_text()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta is not None else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def decode_refresh_token(token: str) -> dict:
    payload = jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("token is not a refresh token")
    return payload


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh tokens cannot be used to authenticate requests")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
