# Stage 4: Upload & Deployment Service Implementation Plan

## Goal
Build the final two pipeline services:
1. **Upload Service** — Consumes `build.completed`, uploads artifacts to MinIO/S3, publishes `deployment.uploaded`
2. **Deployment Service** — Consumes `deployment.uploaded`, configures Caddy routing for live URLs, handles rollbacks, publishes `deployment.live`

## Upload Service Structure
- `app/core/` — config, db, kafka (consumer+producer)
- `app/services/s3_uploader.py` — Async S3 upload via aiobotocore (MinIO-compatible)
- Deterministic S3 keys for idempotent uploads

## Deployment Service Structure
- `app/core/` — config, db, kafka, redis (pub/sub for WebSocket status)
- `app/api/deployments.py` — GET deployments, rollback endpoint
- `app/services/caddy_manager.py` — Dynamic route creation via Caddy Admin API
- `app/services/rollback.py` — Instant rollback by swapping Caddy routes

## Infrastructure Additions (docker-compose.yml)
- **MinIO** — S3-compatible object storage (ports 9000/9001)
- **Caddy** — Reverse proxy with admin API (port 2019) for dynamic routing

## Key Decisions
- MinIO for local dev (S3-compatible, zero code change for production)
- Caddy admin API for dynamic route creation (no config reloads)
- Rollback = re-route (swap S3 path, no rebuild, <500ms)
- Subdomain per project: {project-name}.deployhub.dev
