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
from app.models import User

router = APIRouter()

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
async def login_github():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={quote(settings.GITHUB_CLIENT_ID)}"
        f"&redirect_uri={quote(settings.GITHUB_REDIRECT_URI, safe='')}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)

@router.get("/callback")
async def github_callback(code: str, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
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

@router.post("/refresh")
async def refresh_access_token(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload = decode_refresh_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    _set_refresh_cookie(response, new_refresh_token)

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
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
