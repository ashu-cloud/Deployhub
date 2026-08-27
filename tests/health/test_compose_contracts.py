from __future__ import annotations

import re

import pytest
import yaml

from tests.helpers.paths import COMPOSE_FILE, REPO_ROOT, SERVICES_DIR

COMPOSE_PORTS = {
    "auth-service": 8001,
    "project-service": 8002,
    "build-orchestrator": 8004,
    "upload-service": 8005,
    "deployment-service": 8006,
}


def _compose():
    return yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))


@pytest.mark.health
def test_compose_file_exists():
    assert COMPOSE_FILE.is_file()


@pytest.mark.health
def test_compose_declares_required_infra():
    compose = _compose()
    services = compose.get("services", {})
    for name in ("postgres", "redis", "kafka", "minio", "caddy"):
        assert name in services, f"docker-compose is missing {name}"


@pytest.mark.health
def test_compose_healthchecks_on_stateful_services():
    compose = _compose()
    for name in ("postgres", "redis", "kafka"):
        health = compose["services"][name].get("healthcheck")
        assert health, f"{name} has no healthcheck"


@pytest.mark.security_audit
def test_dockerfile_listen_port_matches_compose_mapping():
    """Host port X:container port X must match the uvicorn --port in the Dockerfile."""
    compose = _compose()
    mismatches = []
    for service, expected_port in COMPOSE_PORTS.items():
        ports = compose["services"][service].get("ports") or []
        mapped = None
        for entry in ports:
            # formats: "8001:8001" or "8001:8000"
            host, container = str(entry).split(":")[-2:]
            mapped = (int(host), int(container.split("/")[0]))
        dockerfile = (SERVICES_DIR / service / "Dockerfile").read_text(encoding="utf-8")
        listen = re.search(r"--port[\"',\s]+(\d+)", dockerfile)
        expose = re.search(r"EXPOSE\s+(\d+)", dockerfile)
        assert listen, f"{service} Dockerfile has no uvicorn --port"
        listen_port = int(listen.group(1))
        if mapped:
            host_port, container_port = mapped
            if container_port != listen_port:
                mismatches.append(
                    f"{service}: compose maps host {host_port}->container {container_port} "
                    f"but uvicorn listens on {listen_port}"
                )
            if host_port != expected_port:
                mismatches.append(f"{service}: expected host port {expected_port}, got {host_port}")
        if expose:
            expose_port = int(expose.group(1))
            if expose_port != listen_port:
                mismatches.append(f"{service}: EXPOSE {expose_port} != listen {listen_port}")
    assert mismatches == [], "Port contract mismatches:\n" + "\n".join(mismatches)


@pytest.mark.health
def test_frontend_rewrites_match_compose_ports():
    config = (REPO_ROOT / "frontend" / "next.config.ts").read_text(encoding="utf-8")
    assert "127.0.0.1:8001" in config
    assert "127.0.0.1:8002" in config
    assert "127.0.0.1:8006" in config
