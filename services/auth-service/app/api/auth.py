from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, get_current_user
from app.services.github import github_service
from app.services.encryption import encryption_service
from app.models import User, OAuthToken
import httpx
import uuid
import secrets
from redis.asyncio import from_url

router = APIRouter()

redis_client = from_url(settings.REDIS_URL, decode_responses=True)

async def check_rate_limit(request: Request):
    client_ip = request.client.host
    endpoint = request.url.path
    key = f"rate_limit:{endpoint}:{client_ip}"
    
    # QUAL-07: Atomic INCR and conditional EXPIRE
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, 60)
    if current > 10: # 10 requests per minute
        raise HTTPException(status_code=429, detail="Too many requests")

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    # Refresh token only -- the access token itself is handed back in the
    # JSON body for the SPA to hold in memory (architecture: RS256 access
    # token stored in memory, RS256 refresh token as HttpOnly+Secure+Strict).
    # Path is "/" so the cookie is sent both to the Next.js rewrite
    # (/api/v1/auth/refresh) and to a direct hit on this service (/auth/refresh).
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


@router.get("/github")
async def login_github(response: Response):
    state = secrets.token_urlsafe(32)
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={quote(settings.GITHUB_CLIENT_ID)}"
        f"&redirect_uri={quote(settings.GITHUB_REDIRECT_URI, safe='')}"
        f"&scope=user:email,repo"
        f"&state={state}"
    )
    redirect = RedirectResponse(url=github_auth_url)
    redirect.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",  # Must be lax for cross-site redirect back
        max_age=600,     # 10 minutes
        path="/",
    )
    return redirect

@router.get("/callback")
async def github_callback(code: str, state: str, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # Verify state parameter to prevent CSRF
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Please try logging in again.")
    
    # 1. Get Access Token
    gh_token = await github_service.get_access_token(code)
    
    # 2. Get User Info
    gh_user = await github_service.get_user_info(gh_token)
    
    # 3. Find or Create User in DB
    github_id = gh_user["id"]
    email = gh_user.get("email") or f"{github_id}@github.deployhub.dev" # fallback if private email
    name = gh_user.get("name") or gh_user.get("login")

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalars().first()

    if not user:
        user = User(github_id=github_id, email=email, name=name)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Save OAuth Token — encrypt before persisting to protect against DB breach.
    token_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    oauth_token = token_result.scalars().first()
    encrypted_token = encryption_service.encrypt(gh_token)
    if oauth_token:
        oauth_token.access_token = encrypted_token
    else:
        oauth_token = OAuthToken(user_id=user.id, access_token=encrypted_token)
        db.add(oauth_token)
    await db.commit()

    # 4. Generate access + refresh tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # 5. Refresh token goes in an HttpOnly cookie; the access token is
    # returned to the client to hold in memory for Authorization headers.
    _set_refresh_cookie(response, refresh_token)

    payload = {
        "message": "Successfully authenticated",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }
    # Browser OAuth is a top-level navigation (Accept: text/html). Send the
    # user back to the SPA, which bootstraps the access token via /auth/refresh.
    # API/test clients still get the JSON body.
    if _wants_html(request):
        redirect = RedirectResponse(url=f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback")
        _set_refresh_cookie(redirect, refresh_token)
        return redirect
    return payload

@router.post("/refresh", dependencies=[Depends(check_rate_limit)])
async def refresh_access_token(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload = decode_refresh_token(token)
    except jwt.PyJWTError:
        # Clear the bad/expired cookie so the browser doesn't keep retrying
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    _set_refresh_cookie(response, new_refresh_token)

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout", dependencies=[Depends(check_rate_limit)])
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    return {"message": "Logged out"}

@router.get("/me")
async def read_users_me(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "email": user.email, "name": user.name}

@router.get("/github/repos")
async def get_github_repos(user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    except Exception:
        uid = user_id

    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == uid))
    oauth_token = result.scalars().first()
    if not oauth_token or not oauth_token.access_token:
        raise HTTPException(status_code=401, detail="GitHub token not found. Please log in again to grant repository access.")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.github.com/user/repos?sort=updated&per_page=100&type=all",
            headers={
                "Authorization": f"Bearer {encryption_service.decrypt(oauth_token.access_token)}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DeployHub-App",
            }
        )
        if response.status_code != 200:
            # Log the raw GitHub error server-side; return a safe generic message
            # to the client (MED-03: prevents leaking internal API details).
            import logging
            logging.getLogger(__name__).error(
                f"GitHub repos fetch failed (status={response.status_code}): {response.text}"
            )
            raise HTTPException(
                status_code=400,
                detail="Failed to fetch repositories from GitHub. Please re-authenticate."
            )
        
        repos = response.json()
        formatted_repos = []
        for r in repos:
            formatted_repos.append({
                "id": str(r.get("id")),
                "name": r.get("name", ""),
                "full_name": r.get("full_name", ""),
                "desc": r.get("description") or "",
                "updated": r.get("updated_at") or "",
                "language": r.get("language") or "Unknown",
            })
        return formatted_repos
