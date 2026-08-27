from functools import lru_cache
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()


class MissingJwtKeyError(RuntimeError):
    """Raised when the RS256 public key has not been provisioned."""


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    path = Path(settings.JWT_PUBLIC_KEY_PATH)
    if not path.is_file():
        raise MissingJwtKeyError(
            f"JWT public key not found at {path}. Run "
            "`python scripts/generate_secrets.py` and mount secrets/jwt into this service."
        )
    return path.read_text()


def get_current_user_from_token(token: str) -> str:
    """Decode and validate a raw bearer token string (used by HTTP + WebSocket routes)."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        payload = jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh tokens cannot be used to authenticate requests")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return get_current_user_from_token(credentials.credentials)
