from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.services.github import github_service
from app.models import User

router = APIRouter()

@router.get("/github")
async def login_github():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=user:email"
    )
    return RedirectResponse(url=github_auth_url)

@router.get("/callback")
async def github_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
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

    # 4. Generate JWT
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # 5. Set Cookie or return JSON (Returning JSON for now for easy testing)
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True, 
        secure=True, 
        samesite="lax"
    )
    
    return {
        "message": "Successfully authenticated",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id)
    }

@router.get("/me")
async def read_users_me():
    # Will implement Depends(get_current_user) later
    return {"message": "Requires JWT implementation"}
