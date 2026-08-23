# System Flow Deep Dive

This document provides a step-by-step trace of the critical paths within the DeployHub ecosystem. It bridges the gap between the high-level architecture diagram and the actual code execution, showing exactly how data flows across services, databases, and message brokers.

---

## Flow 1: The Automated Deployment Pipeline
*(What happens when a user pushes code to GitHub?)*

This is the most critical and complex flow in the system. It leverages a **Choreography Saga Pattern** to manage the distributed transaction.

### Step 1: The Webhook Trigger
1. **GitHub** sends a `POST` request to `https://api.deployhub.dev/webhook/github/{project_id}`.
2. The **APISIX Gateway** receives the request. It bypasses JWT authentication (since GitHub doesn't have a user token) but applies a specific rate limit.
3. The request hits the **Dedicated Webhook Receiver** (part of the Project Service but exposed via a fast-path endpoint).
4. The receiver immediately validates the `X-Hub-Signature-256` HMAC to prove the request genuinely came from GitHub.
5. If valid, it publishes a `build.queued` event to **Kafka** (Topic: `build.queued`, Partition Key: `project_id`).
6. It immediately returns an HTTP 200 OK to GitHub. *(Total time: < 10ms)*.

### Step 2: Build Orchestration
1. A pod in the **Build Orchestrator** service (consuming the `build.queued` topic) picks up the message.
2. The orchestrator attempts to acquire a **Redis Distributed Lock** for that `project_id`.
   - *Why?* To prevent concurrent builds for the same project from corrupting the state.
3. Once locked, it connects to **PostgreSQL** to update the deployment row: `UPDATE deployments SET status = 'building' WHERE id = X AND status = 'queued'`.
4. It spins up an isolated **Docker Container** with resource limits (512MB RAM, no network).
5. The container clones the repo and runs the build command (e.g., `npm run build`).

### Step 3: Real-Time Log Streaming
1. As the Docker container builds, it outputs logs to stdout.
2. The **Build Orchestrator** continuously reads this stream and publishes each line to **Kafka** (Topic: `build.logs.{deployment_id}`).
3. Two consumers process these logs:
   - **Log Archiver Consumer:** Reads the logs in batches and writes them to the partitioned `build_logs` PostgreSQL table for permanent storage.
   - **Centrifugo Consumer:** Reads the logs and immediately publishes them to **Redis Pub/Sub**. Centrifugo pushes them over WebSockets directly to the user's browser in real-time.

### Step 4: Artifact Upload
1. The Docker build completes successfully.
2. The Build Orchestrator zips the output directory (e.g., `.next/` or `dist/`).
3. It publishes a `build.completed` event to Kafka.
4. The **Upload Service** consumes this event, retrieves the zipped artifact, and streams it to **AWS S3 / MinIO**.
5. Upon successful upload, it publishes a `deployment.uploaded` event.

### Step 5: Traffic Routing (Go-Live)
1. The **Deployment Service** consumes `deployment.uploaded`.
2. It makes an API call to the internal **Caddy Reverse Proxy** to update the routing rules.
3. Caddy is instructed to route traffic for `projectname-hash.deployhub.dev` to the S3 bucket path containing the static assets (or the serverless runner).
4. Caddy hot-reloads its configuration with zero downtime.
5. The Deployment Service updates the Postgres row: `status = 'live'` and publishes a `deployment.live` event.
6. The user's dashboard UI (listening via WebSocket) turns green and displays the live URL.

---

## Flow 2: Rollback to a Previous Deployment
*(What happens when a user clicks "Rollback"?)*

Because deployments are **Immutable** (we never overwrite an old build's files in S3), rolling back is incredibly fast.

1. User clicks "Rollback to Deployment #5" on the frontend.
2. The frontend sends an authenticated `POST /deployments/{id}/rollback` to the API Gateway.
3. The gateway validates the JWT and routes it to the **Deployment Service**.
4. The service queries **PostgreSQL** to retrieve the S3 path of Deployment #5.
5. The service calls the **Caddy API** to instantly update the route for the project's custom domain to point to Deployment #5's S3 path.
6. The database is updated: Deployment #6 is marked as `rolled_back`, and Deployment #5 is marked as `live`.
7. A `deployment.rollback` event is fired to notify the frontend via WebSockets.
8. The entire process takes ~200-500ms. No builds or uploads are required.

---

## Flow 3: Auto-Scaling under High Traffic (Handling Viral Sites)

When a deployed site gets viral traffic, the platform protects itself.

1. **Edge Caching:** If configured, Cloudflare serves the cached assets directly.
2. **APISIX Rate Limiting:** If traffic bypasses the cache, APISIX tracks the requests per IP and applies the configured limits.
3. **Database Protection:** The stateless backend services autoscale via Kubernetes HPA. However, PostgreSQL cannot instantly scale horizontally. **PgBouncer** queues the database connections, ensuring the database is never overwhelmed by too many active queries, even if there are 100 backend pods asking for data. The worst-case scenario is increased latency, not a database crash.
