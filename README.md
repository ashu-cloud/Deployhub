<div align="center">
  <h1>DeployHub ⚡</h1>
  <p><strong>A production-grade, distributed deployment platform inspired by Vercel.</strong></p>
  <p>Built to handle real-time logs, isolated container builds, and zero-downtime routing at scale.</p>
</div>

<br />

## 🌟 Why This Project Stands Out

Most portfolio projects are simple CRUD applications. **DeployHub is a distributed system.** It was architected from the ground up to solve complex backend engineering problems:

- **Choreography Saga Pattern:** A fully event-driven CI/CD pipeline using **Apache Kafka** to decouple builds, uploads, and routing, guaranteeing fault tolerance and exactly-once processing.
- **Strict Concurrency Control:** Prevents race conditions during simultaneous webhooks using **Redis Distributed Locks** and **PostgreSQL Optimistic Concurrency** (row-level versioning).
- **Secure Build Isolation:** Untrusted user code is executed in ephemeral **Docker** containers with dropped network access, read-only filesystems, and strict CPU/Memory limits.
- **Massive Real-Time Streaming:** Streams Docker build `stdout` directly to the browser with minimal latency using **Kafka**, **Redis Pub/Sub**, and **Centrifugo WebSockets** (capable of handling 100k+ concurrent connections).
- **Sub-500ms Zero-Downtime Rollbacks:** Decouples immutable artifact storage (S3/MinIO) from the reverse proxy (Caddy), allowing instant traffic rerouting via Unix socket APIs without rebuilding.

---

## 🏗️ Architecture & Tech Stack

The platform is split into 5 stateless microservices, an API gateway, an event stream, and a robust data layer.

**Core Stack:**
- **Backend Services:** Python, FastAPI, `asyncio`, Pydantic
- **Event Streaming:** Apache Kafka (Confluent Cloud)
- **Database:** PostgreSQL (Neon Serverless HA) + PgBouncer
- **Caching & Locks:** Redis (Upstash)
- **API Gateway:** Apache APISIX (Rate limiting, JWT Auth)
- **Real-time WebSockets:** Centrifugo
- **Infrastructure:** Docker, Kubernetes (GKE), Caddy

> **Deep Dive:** I have extensively documented the systemic thinking, tradeoffs, and architectural decisions behind this stack. If you are an engineer or hiring manager reviewing my code, **please start here:**
> 1. 📘 [Architecture Overview](./docs/architecture.md)
> 2. ⚖️ [Tradeoffs & Design Decisions](./docs/tradeoffs_and_decisions.md)
> 3. 🔍 [System Flow Deep Dive (The CI/CD Saga)](./docs/system_flow_deep_dive.md)

---

## 🛡️ Security & Reliability Engineering

- **Zero-Trust JWT Rotation:** Downstream microservices authenticate requests using only RS256 public keys. Access tokens expire in 15 minutes; long-lived refresh tokens are strictly `HttpOnly` and `Secure`.
- **Encrypted Secrets:** User environment variables are encrypted at rest using AES-256. Webhooks are strictly verified via `X-Hub-Signature-256` HMAC.
- **Cascading Failure Protection:** External integrations (GitHub API, S3, Caddy) are wrapped in **Circuit Breakers**, **Bulkhead Semaphores**, and **Exponential Backoff Retries**.
- **Idempotency:** Every consumer and mutating API endpoint enforces idempotency keys, rendering duplicate GitHub webhook deliveries harmless.

---

## 🚀 Running Locally

The entire distributed system can be spun up locally using Docker Compose.

```bash
# 1. Generate local RS256 JWT keypairs and AES encryption secrets.
# (These are gitignored and never hardcoded in the codebase).
pip install cryptography
python scripts/generate_secrets.py

# 2. Start the backend microservices, Kafka, Redis, Postgres, and MinIO.
docker-compose --env-file secrets/compose.env up -d --build

# 3. Start the Next.js frontend
cd frontend
npm install
npm run dev
```

*Note: GitHub OAuth requires an OAuth App configured with the callback URL `http://localhost:3000/api/v1/auth/callback`.*

---
<div align="center">
  <i>Designed and engineered by Ashu Panchal.</i>
</div>
