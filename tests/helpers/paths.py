from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = REPO_ROOT / "services"
FRONTEND_DIR = REPO_ROOT / "frontend"
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"
CADDYFILE = REPO_ROOT / "infra" / "caddy" / "Caddyfile"
