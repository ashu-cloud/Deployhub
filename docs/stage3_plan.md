# Stage 3: Build Orchestrator Implementation Plan

## Goal
Build the **Build Orchestrator** — the Kafka consumer that clones repos, runs isolated Docker builds, streams logs in real-time via Redis Pub/Sub, and publishes completion/failure events.

## Service Structure
- `app/main.py` — FastAPI + Kafka consumer lifespan
- `app/core/` — config, db, kafka (consumer+producer), redis (pub/sub + locks)
- `app/services/builder.py` — Core build pipeline orchestration
- `app/services/docker_runner.py` — Docker container lifecycle (aiodocker)
- `app/services/log_streamer.py` — Real-time log streaming to Redis Pub/Sub
- `app/models.py` — Deployment model for status updates

## Build Pipeline Flow
1. Consume `build.queued` from Kafka
2. Acquire Redis distributed lock for project_id
3. Update deployment status: queued → building
4. Clone repo (git clone --depth=1)
5. Detect framework (package.json, requirements.txt, Dockerfile)
6. Run Docker container (512MB RAM, 1 CPU, 10-min timeout)
7. Stream logs → Redis Pub/Sub (real-time) + Kafka (archival)
8. On success: publish `build.completed`
9. On failure: publish `build.failed`
10. Release lock, commit Kafka offset

## Key Design Decisions
- Manual Kafka offset commit (crash → automatic retry)
- aiodocker for async container management
- Redis Pub/Sub for real-time logs (low latency)
- Distributed locking prevents duplicate builds per project
