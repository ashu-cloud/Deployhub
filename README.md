# DeployHub ⚡

> Designed & Engineered by Ashu Panchal

DeployHub is a production-grade, distributed deployment platform inspired by Vercel. It allows developers to connect their GitHub repositories and automatically build, deploy, and host their web applications with a single click.

This project was built to demonstrate advanced system design patterns, distributed architecture, and highly scalable microservices capable of handling real-time logs and zero-downtime deployments.

## 🌟 Core Features

- **Automated CI/CD Pipeline:** Push to GitHub and DeployHub automatically handles the build, containerization, and routing.
- **Real-Time Build Logs:** Watch your build progress live via WebSockets (Centrifugo + Redis Pub/Sub).
- **Zero-Downtime Deployments:** Traffic is seamlessly routed to the new deployment once it's healthy.
- **Instant Rollbacks:** Revert to a previous deployment version in less than 500ms.
- **Environment Variable Management:** Secure, encrypted-at-rest storage for sensitive configuration.
- **Highly Available Architecture:** Designed with no single point of failure.

## 🏗️ Tech Stack

DeployHub is built on a modern, robust technology stack:

- **Frontend:** Next.js (React), Tailwind CSS, TypeScript, Framer Motion
- **API Gateway:** Apache APISIX
- **Microservices:** FastAPI (Python), asyncio, httpx
- **Event Streaming:** Apache Kafka (Confluent Cloud)
- **Database:** PostgreSQL (Neon Serverless, HA)
- **Caching & Locking:** Redis (Upstash)
- **Real-time WebSockets:** Centrifugo
- **Container Orchestration:** Docker, Kubernetes (GKE)

## 📚 Documentation & Architecture Deep Dive

This repository contains extensive documentation detailing the internal workings of the platform. If you want to understand how this system scales and why specific technical decisions were made, start here:

1. [Architecture Overview](./docs/architecture.md) - The master design document covering the API Gateway, Microservices, Event Layer, Data Layer, and Scaling strategies.
2. [Tradeoffs & Design Decisions](./docs/tradeoffs_and_decisions.md) - A deep dive into *why* certain technologies were chosen (e.g., FastAPI vs Node.js, Kafka vs RabbitMQ) and the pros and cons of those decisions.
3. [System Flow Deep Dive](./docs/system_flow_deep_dive.md) - Step-by-step trace of critical paths, such as what exactly happens when a webhook is received from GitHub.

## 🚀 Running Locally

The project includes a `docker-compose.yml` for local development.

```bash
# One-time: generate a local RS256 JWT keypair + webhook/encryption secrets.
# Writes to ./secrets/ -- gitignored, never committed.
pip install cryptography
python scripts/generate_secrets.py

# Start all dependent services (--env-file feeds docker-compose's ${VAR} substitution)
docker-compose --env-file secrets/compose.env up -d --build

# Install backend dependencies
cd services/project-service
python -m venv .venv
source .venv/bin/activate  # (On Windows use: .venv\Scripts\activate)
pip install -e .
uvicorn app.main:app --reload --port 8002

# Install frontend dependencies and run Next.js
cd ../../frontend
npm install
npm run dev
```

Every service fails fast (refuses to start) if its JWT keys / webhook secret /
encryption key aren't present -- there are no insecure hardcoded defaults.
Re-run `python scripts/generate_secrets.py` any time; it never overwrites
existing secrets.

## 🔐 Security & Reliability

DeployHub implements several layers of defense and reliability:
- **RS256 JWTs:** auth-service holds the private signing key; every other service only ever holds the public key, so a compromised downstream service can never mint tokens.
- **Refresh-token rotation:** short-lived (15 min) access tokens are handed to the client to hold in memory; a long-lived refresh token lives only in an HttpOnly + Secure + SameSite=Strict cookie.
- **No hardcoded secrets:** JWT keys, the webhook HMAC secret, and the AES-256 env-var encryption key are never committed -- see `scripts/generate_secrets.py`.
- **Rate Limiting:** Redis-backed per-user limits on project creation at the service layer (defense in depth beneath any gateway-level limiting).
- **Circuit Breakers & Retries:** Protection against cascading failures for all external calls (GitHub API, S3, Caddy).
- **Idempotency:** Every consumer and mutating API endpoint is idempotent to prevent duplicate deployments.
- **Row-Level Locking:** Optimistic concurrency control in PostgreSQL for strict deployment state machine transitions.
- **Caddy admin API:** never bound to a network interface -- reachable only over a Unix socket shared with deployment-service.

---
Crafted with ink & code.
