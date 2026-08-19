# Stage 1: Infrastructure Scaffold & Auth Service Implementation Plan

## Goal Description
Set up the core monorepo structure, local development environment (Postgres, Redis, Kafka via Docker Compose), and build the **Auth Service** (Tier 1 feature) with GitHub OAuth integration. This establishes the foundation for all future microservices.

## Proposed Changes

### 1. Monorepo Infrastructure

#### [NEW] docker-compose.yml
- **PostgreSQL 15**: For all relational data (projects, users, deployments)
- **Redis (latest)**: For caching, JWT blocklist, and distributed locks
- **Redpanda (Kafka alternative)**: A lightweight, Kafka API-compatible broker that runs beautifully in a single container for local dev (no Zookeeper needed).

### 2. Global Tooling

#### [NEW] pyproject.toml (Root level - Optional workspace setup)
- We will use **`uv`** as our Python package manager. It is blazingly fast and standard for modern FastAPI projects.
- We will initialize the monorepo workspace for Python.

### 3. Auth Service

#### [NEW] services/auth-service/
We will create the Auth Service directory with the following structure:
- `app/main.py`: FastAPI entry point
- `app/core/config.py`: Environment variable loading (Pydantic BaseSettings)
- `app/core/db.py`: SQLAlchemy async engine and base models
- `app/api/auth.py`: OAuth routes (`/auth/github`, `/auth/callback`, `/auth/me`)
- `app/services/github.py`: Async GitHub API integration (httpx)
- `app/schemas/`: Pydantic models for request/response validation
- `pyproject.toml` (local to auth-service)

#### [NEW] services/auth-service/Dockerfile
- Standard Python 3.11/3.12 slim Dockerfile optimized for `uv`.

## Verification Plan

### Automated Tests
- N/A for this initial scaffold, but we will ensure the service boots successfully and connects to the database.

### Manual Verification
1. Run `docker compose up -d` to spin up Postgres, Redis, and Redpanda.
2. Run `uvicorn app.main:app --reload --port 8000` inside `services/auth-service`.
3. Verify the `/health` endpoint returns 200 OK.
4. Verify the database tables (`users`, `oauth_tokens`) are created automatically via SQLAlchemy/Alembic on startup.
