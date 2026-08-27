import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def _build_admin_client(admin_url: str) -> httpx.AsyncClient:
    """Caddy's admin API is exposed over a Unix socket, never a network port.

    ``CADDY_ADMIN_URL`` of the form ``unix:///path/to.sock`` is translated
    into an httpx client that dials that socket directly; anything else
    (e.g. for local, non-Docker development) falls back to a normal
    base-url HTTP client.
    """
    if admin_url.startswith("unix://"):
        socket_path = admin_url[len("unix://"):]
        if not socket_path.startswith("/"):
            socket_path = "/" + socket_path
        transport = httpx.AsyncHTTPTransport(uds=socket_path)
        return httpx.AsyncClient(transport=transport, base_url="http://caddy-admin")
    return httpx.AsyncClient(base_url=admin_url)

class CaddyManager:
    def __init__(self):
        # httpx client for interacting with Caddy's REST Admin API
        self.client = _build_admin_client(settings.CADDY_ADMIN_URL)

    async def add_route(self, subdomain: str, s3_path: str):
        """
        Dynamically adds a route to Caddy to reverse proxy the subdomain 
        to the MinIO/S3 bucket path.
        """
        # The target is the MinIO S3 bucket URL
        # e.g., http://minio:9000/deployhub-artifacts/deployments/{project_id}/{deployment_id}/
        
        # Caddy's config is represented as JSON. We add a route to the default server.
        # This is a simplified Caddy API payload for reverse proxying
        
        target_url = f"http://deployhub_minio:9000/deployhub-artifacts/{s3_path}"
        
        route_config = {
            "match": [{"host": [f"{subdomain}.{settings.BASE_DOMAIN}"]}],
            "handle": [{
                "handler": "reverse_proxy",
                "upstreams": [{"dial": "deployhub_minio:9000"}],
                "headers": {
                    "request": {
                        "set": {
                            "Host": ["deployhub_minio:9000"]
                        }
                    }
                },
                # We need to rewrite the URI to prepend the S3 bucket path
                "rewrite": {
                    "uri": f"/deployhub-artifacts/{s3_path}{{http.request.uri}}"
                }
            }]
        }
        
        try:
            # We append the route to Caddy's route list dynamically
            resp = await self.client.post("/config/apps/http/servers/srv0/routes", json=route_config)
            resp.raise_for_status()
            logger.info(f"Successfully added Caddy route for {subdomain}.{settings.BASE_DOMAIN} -> {s3_path}")
        except httpx.HTTPStatusError as e:
            # If Caddy isn't perfectly configured with srv0, it might 404. 
            # In a real setup, we ensure Caddyfile has a basic server block first.
            logger.error(f"Caddy API error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to communicate with Caddy: {e}")
            raise

caddy_manager = CaddyManager()
