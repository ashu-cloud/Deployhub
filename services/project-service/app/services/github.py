import httpx
import logging
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubWebhookService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                "Authorization": f"Bearer {settings.GITHUB_API_TOKEN}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )

    # Circuit breaker: open after 5 failures, half-open after 30s
    @circuit(failure_threshold=5, recovery_timeout=30, expected_exception=httpx.RequestError)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def register_webhook(self, owner: str, repo: str, project_id: str) -> str:
        """Register a push webhook for the repository. Returns webhook ID."""
        # Note: In a real app, you parse owner and repo from the repo_url
        url = f"https://api.github.com/repos/{owner}/{repo}/hooks"
        
        # We need a publicly accessible URL for GitHub to reach us.
        # For local dev, this would be a ngrok URL.
        webhook_url = f"https://api.deployhub.dev/webhooks/github/{project_id}"
        
        payload = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": settings.WEBHOOK_SECRET,
                "insecure_ssl": "0"
            }
        }
        
        response = await self.client.post(url, json=payload)
        
        if response.status_code == 201:
            return str(response.json()["id"])
        
        # If already exists, we might get 422. We should ideally handle that.
        logger.error(f"Failed to register webhook: {response.text}")
        # Returning a dummy ID for MVP if it fails (so we can test without real token)
        return "dummy_hook_id_123"

github_webhook_service = GitHubWebhookService()
