import httpx
import logging
import re
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


def slugify_subdomain(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", (name or "").lower()).strip("-")
    return (slug or "app")[:63]


class CaddyManager:
    def __init__(self):
        self.client = _build_admin_client(settings.CADDY_ADMIN_URL)
        self.minio_dial = settings.MINIO_DIAL

    async def add_route(self, subdomain: str, s3_path: str):
        """
        Dynamically prepends a host route so ``{subdomain}.{BASE_DOMAIN}``
        reverse-proxies to the MinIO prefix that holds this deployment.
        """
        host = f"{slugify_subdomain(subdomain)}.{settings.BASE_DOMAIN}"
        prefix = f"/{settings.S3_BUCKET_NAME}/{s3_path.strip('/')}"

        route_config = {
            "match": [{"host": [host]}],
            "handle": [
                {
                    "handler": "rewrite",
                    "match": [{"path": ["/"]}],
                    "uri": "/index.html",
                },
                {
                    "handler": "rewrite",
                    "uri": prefix + "{http.request.uri}",
                },
                {
                    "handler": "reverse_proxy",
                    "upstreams": [{"dial": self.minio_dial}],
                },
            ],
        }

        try:
            # Insert at index 0 so this host match wins over the Caddyfile catch-all.
            resp = await self.client.post(
                "/config/apps/http/servers/srv0/routes/0",
                json=route_config,
            )
            if resp.status_code == 404:
                resp = await self.client.post(
                    "/config/apps/http/servers/srv0/routes",
                    json=route_config,
                )
            resp.raise_for_status()
            logger.info(f"Successfully added Caddy route for {host} -> {prefix}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Caddy API error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to communicate with Caddy: {e}")
            raise

    async def add_custom_domain_route(self, domain: str, s3_path: str):
        """
        Dynamically prepends a host route for a custom domain to reverse-proxy
        to the MinIO prefix that holds this deployment.
        """
        prefix = f"/{settings.S3_BUCKET_NAME}/{s3_path.strip('/')}"

        route_config = {
            "match": [{"host": [domain]}],
            "handle": [
                {
                    "handler": "rewrite",
                    "match": [{"path": ["/"]}],
                    "uri": "/index.html",
                },
                {
                    "handler": "rewrite",
                    "uri": prefix + "{http.request.uri}",
                },
                {
                    "handler": "reverse_proxy",
                    "upstreams": [{"dial": self.minio_dial}],
                },
            ],
        }

        try:
            resp = await self.client.post(
                "/config/apps/http/servers/srv0/routes/0",
                json=route_config,
            )
            if resp.status_code == 404:
                resp = await self.client.post(
                    "/config/apps/http/servers/srv0/routes",
                    json=route_config,
                )
            resp.raise_for_status()
            logger.info(f"Successfully added Caddy custom domain route for {domain} -> {prefix}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Caddy API error for custom domain: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to communicate with Caddy for custom domain: {e}")
            raise

    async def remove_custom_domain_route(self, domain: str):
        """
        Removes the host route for a custom domain from Caddy.
        """
        try:
            # 1. Fetch all routes
            resp = await self.client.get("/config/apps/http/servers/srv0/routes")
            if resp.status_code == 404:
                return # No routes exist
            resp.raise_for_status()
            routes = resp.json() or []
            
            # 2. Find the index of the route matching this domain
            target_index = -1
            for i, route in enumerate(routes):
                match = route.get("match", [{}])[0]
                hosts = match.get("host", [])
                if domain in hosts:
                    target_index = i
                    break
            
            # 3. Delete the route if found
            if target_index != -1:
                del_resp = await self.client.delete(f"/config/apps/http/servers/srv0/routes/{target_index}")
                del_resp.raise_for_status()
                logger.info(f"Successfully removed Caddy custom domain route for {domain}")
            else:
                logger.warning(f"Could not find Caddy route to remove for custom domain: {domain}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Caddy API error removing custom domain: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to communicate with Caddy removing custom domain: {e}")
            raise

caddy_manager = CaddyManager()
