import httpx
from fastapi import HTTPException
from app.core.config import settings

class GitHubService:
    def __init__(self):
        self.client_id = settings.GITHUB_CLIENT_ID
        self.client_secret = settings.GITHUB_CLIENT_SECRET
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def get_access_token(self, code: str) -> str:
        url = "https://github.com/login/oauth/access_token"
        headers = {"Accept": "application/json"}
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        }
        response = await self.http_client.post(url, data=data, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
            
        json_data = response.json()
        if "error" in json_data:
            raise HTTPException(status_code=400, detail=json_data.get("error_description", "GitHub OAuth Error"))
            
        return json_data["access_token"]

    async def get_user_info(self, access_token: str) -> dict:
        url = "https://api.github.com/user"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = await self.http_client.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")
            
        return response.json()

github_service = GitHubService()
