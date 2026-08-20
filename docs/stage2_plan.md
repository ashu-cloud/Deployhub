# Stage 2: Project Service Implementation Plan

## Goal
Build the **Project Service** — the core microservice that manages project lifecycle: connecting GitHub repos, registering webhooks automatically, storing encrypted environment variables, and publishing `build.queued` events to Kafka when pushes arrive.

## Proposed Changes

### 1. Project Service Scaffold
Same structure as auth-service:
- `app/main.py` — FastAPI app + lifespan
- `app/core/` — config, db, security (JWT decode), kafka producer
- `app/api/` — projects CRUD, env_vars, webhooks receiver
- `app/services/` — GitHub webhook registration, AES encryption
- `app/models.py` — Project, EnvVar, CustomDomain, Deployment tables

### 2. Database Models (4 tables)
- **projects** — id, user_id, repo_name, repo_url, github_webhook_id, status, created_at
- **environment_variables** — id, project_id, key, encrypted_value, created_at
- **custom_domains** — id, project_id, domain, verified, ssl_cert_id, created_at
- **deployments** — id, project_id, git_commit, git_branch, status, s3_path, deployment_number, deployed_at, created_at, version (optimistic locking)

### 3. API Endpoints
- POST/GET/PUT/DELETE /projects (CRUD, JWT protected)
- POST/GET/DELETE /projects/{id}/env-vars (encrypted)
- POST /webhooks/github/{project_id} (HMAC validated, publishes to Kafka)

### 4. Key Integrations
- GitHub API for webhook registration (circuit breaker + retry)
- AES-256-GCM encryption for environment variables
- aiokafka producer for `build.queued` events
- Redis for webhook idempotency (X-GitHub-Delivery)

## Verification Plan
1. Boot project-service on port 8002
2. Verify /health returns 200
3. Verify all 4 tables are created
4. Test project CRUD via Swagger UI
5. Test env var encryption round-trip
