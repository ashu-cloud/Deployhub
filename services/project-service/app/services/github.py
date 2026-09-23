import httpx
import logging
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)

class GitHubWebhookService:
    def __init__(self):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        # An empty `Bearer ` header value is illegal (httpx raises
        # LocalProtocolError, which crashed the whole request/connection
        # instead of a normal 401 from GitHub). Only send the header when a
        # real token is configured; without one, GitHub API calls simply fail
        # with 401 and we fall through to the no-token path below.
        if settings.GITHUB_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_API_TOKEN}"
        self.client = httpx.AsyncClient(timeout=10.0, headers=headers)

    # Circuit breaker: open after 5 failures, half-open after 30s
    @circuit(failure_threshold=5, recovery_timeout=30, expected_exception=httpx.RequestError)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def register_webhook(self, owner: str, repo: str, project_id: str) -> str | None:
        """Register a push webhook for the repository. Returns webhook ID, or None if registration failed."""
        url = f"https://api.github.com/repos/{owner}/{repo}/hooks"

        # We need a publicly accessible URL for GitHub to reach us.
        # For local dev, this would be a ngrok/cloudflare-tunnel URL.
        webhook_url = f"{settings.WEBHOOK_BASE_URL.rstrip('/')}/webhooks/github/{project_id}"

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

        try:
            response = await self.client.post(url, json=payload)
        except httpx.HTTPError as exc:
            # Covers auth/connection/protocol errors (e.g. no GITHUB_API_TOKEN) --
            # never let a GitHub API hiccup take down project creation.
            logger.error(f"GitHub webhook registration request failed: {exc}")
            return None

        if response.status_code == 201:
            return str(response.json()["id"])

        # 422 = hook already exists; log and continue without a stored ID.
        logger.error(f"Failed to register webhook (status={response.status_code}): {response.text}")
        return None

github_webhook_service = GitHubWebhookService()
