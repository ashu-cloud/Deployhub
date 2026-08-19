# Production Architecture — Deployment Platform

> A battle-hardened, fail-proof distributed system designed for high throughput, horizontal scalability, and zero-downtime operations.

---

## Table of Contents
1. [System Design Principles](#1-system-design-principles)
2. [High-Level Architecture Diagram](#2-high-level-architecture-diagram)
3. [Traffic Ingress & API Gateway Layer](#3-traffic-ingress--api-gateway-layer)
4. [Microservices Architecture](#4-microservices-architecture)
5. [Event Streaming Layer (Kafka)](#5-event-streaming-layer-kafka)
6. [Data Layer](#6-data-layer)
7. [Caching Strategy (Redis)](#7-caching-strategy-redis)
8. [Build Orchestration at Scale](#8-build-orchestration-at-scale)
9. [Real-Time Layer (WebSocket)](#9-real-time-layer-websocket)
10. [Concurrency & Distributed Locking](#10-concurrency--distributed-locking)
11. [Resilience Patterns](#11-resilience-patterns)
12. [Observability Stack](#12-observability-stack)
13. [Infrastructure Topology (GKE)](#13-infrastructure-topology-gke)
14. [Security Architecture](#14-security-architecture)
15. [Data Flow: Critical Paths](#15-data-flow-critical-paths)
16. [Scaling Runbook](#16-scaling-runbook)

---

## 1. System Design Principles

These are the non-negotiable constraints that every architectural decision is derived from:

| Principle | Implementation |
|---|---|
| **Fail-fast, recover fast** | Circuit breakers on every external call, health checks every 5s |
| **No single point of failure** | Every stateless service has ≥2 replicas; stateful via managed HA |
| **Async over sync** | All heavy work goes through Kafka; HTTP only for queries/commands |
| **Idempotency everywhere** | Every consumer, every write is idempotent (duplicate-safe) |
| **Immutable deployments** | Deployments are never mutated; a new deployment replaces old |
| **Backpressure awareness** | Producers slow down when consumers are overwhelmed |
| **Defense in depth** | Auth at gateway, service, and data layer |

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                   │
│        Browser / CLI / GitHub Webhooks                          │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTPS / WSS
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              APISIX GATEWAY CLUSTER (2+ replicas)               │
│  - Request routing         - JWT validation                      │
│  - Global rate limiting    - Plugin chain (auth, logging, cors)  │
│  - Load balancing          - Request/response transformation     │
└──────┬──────────────────────────────────────────────────────────┘
       │ Routes to services based on path prefix
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                   SERVICE MESH (Istio / Linkerd)                  │
│   mTLS between all services · Traffic policies · Retry rules     │
│                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐  │
│  │ Auth Service │ │Project Svc   │ │  Deployment Service      │  │
│  │  (2 pods)    │ │  (2 pods)    │ │     (2 pods)             │  │
│  └──────────────┘ └──────────────┘ └──────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────┐ ┌──────────────────────────────┐   │
│  │  Build Orchestrator      │ │  Upload Service              │   │
│  │  (3 pods, auto-scales)   │ │  (2 pods)                    │   │
│  └──────────────────────────┘ └──────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────┐ ┌──────────────────────────────┐   │
│  │  AI Service (1-2 pods)   │ │  Centrifugo (2 pods, WSS)    │   │
│  └──────────────────────────┘ └──────────────────────────────┘   │
└──────┬──────────┬────────────────────────────────────────────────┘
       │          │
       ▼          ▼
┌────────────┐  ┌────────────────────────────────────────────────┐
│   Kafka    │  │               DATA LAYER                        │
│  Cluster   │  │  ┌──────────────┐  ┌─────────┐  ┌──────────┐  │
│ (3 brokers │  │  │  PostgreSQL  │  │  Redis  │  │  S3/R2   │  │
│  KRaft)    │  │  │  (Neon HA)   │  │ Cluster │  │ (CDN)    │  │
└────────────┘  │  └──────────────┘  └─────────┘  └──────────┘  │
                └────────────────────────────────────────────────┘
```

---

## 3. Traffic Ingress & API Gateway Layer

> **Note:** Cloudflare and CDN have been removed from this architecture (resume project). APISIX is the first line of defense. TLS is handled by Caddy (Let's Encrypt auto-cert). Rate limiting is enforced at the APISIX layer.

### 3.1 APISIX Gateway (First Line of Defense)
Two or more replicas behind a Network Load Balancer.

**Critical Plugins Enabled:**
```yaml
# Per-route configuration example
routes:
  - id: build-logs-stream
    uri: /deployments/*/logs
    plugins:
      jwt-auth: {}          # validate JWT before any service hit
      limit-req:
        rate: 100           # 100 req/s per user
        burst: 50
      response-rewrite: {}
      cors:
        allow_origins: "https://app.deployhub.dev"
    upstream:
      nodes:
        deployment-service:8000: 1
      type: roundrobin
      checks:              # active health checking
        active:
          http_path: /health
          interval: 5
          unhealthy:
            http_failures: 2
```

**Rate Limiting Strategy (multi-tier):**
| Tier | Limit | Scope |
|---|---|---|
| Global (Cloudflare) | 5000 req/min | Per IP |
| API Gateway | 1000 req/min | Per user JWT |
| Build Trigger | 10 builds/min | Per project |
| GitHub Webhook | 500 req/min | Per IP whitelist |

### 3.3 Webhook Receiver (Dedicated)
GitHub webhooks go to a **separate, dedicated lightweight service** (not through the main gateway flow), reasons:
- GitHub webhook IPs are known and whitelisted — no auth overhead.
- Need to validate `X-Hub-Signature-256` HMAC, then publish to Kafka immediately.
- Must respond with HTTP 200 within 10 seconds or GitHub marks delivery as failed.
- Decoupled from all other services — a build system outage won't fail webhook receipts.

```python
# Pattern: receive → validate HMAC → publish to Kafka → return 200 immediately
# Processing happens entirely asynchronously downstream
@app.post("/webhook/github/{project_id}")
async def receive_webhook(project_id: str, request: Request):
    body = await request.body()
    validate_github_signature(request.headers, body)  # fail fast
    await kafka_producer.send("build.queued", build_event)
    return {"status": "accepted"}  # instant 200, no processing
```

---

## 4. Microservices Architecture

### 4.1 Service Design Patterns

Every microservice follows this internal structure:

```
service/
├── app/
│   ├── main.py             # FastAPI app factory
│   ├── api/                # Route handlers (thin controllers)
│   ├── services/           # Business logic layer
│   ├── repositories/       # Data access layer (DB queries)
│   ├── events/             # Kafka producer/consumer
│   ├── schemas/            # Pydantic models (in, out, events)
│   ├── core/
│   │   ├── config.py       # Pydantic BaseSettings
│   │   ├── db.py           # SQLAlchemy async engine
│   │   ├── redis.py        # Redis client
│   │   ├── kafka.py        # Kafka client factory
│   │   ├── circuit_breaker.py
│   │   └── middleware.py   # Tracing, logging, error handlers
│   └── health.py           # /health and /ready endpoints
├── tests/
├── Dockerfile
└── pyproject.toml
```

### 4.2 Async-First FastAPI Pattern

Every service uses `asyncio` and async database drivers — no blocking I/O ever.

```python
# Example: Async DB access with connection pooling
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # per pod
    max_overflow=10,        # burst capacity
    pool_timeout=30,
    pool_recycle=1800,      # recycle connections every 30 min
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency injection per request
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 4.3 Inter-Service Communication Rules

| Scenario | Pattern | Why |
|---|---|---|
| Query another service | **Async HTTP via httpx** | Simple, traceable |
| Trigger work in another service | **Kafka event** | Decoupled, retryable |
| Real-time state check | **Redis** | Low latency |
| Never | **Direct DB access across services** | Hard boundary |

**httpx client with circuit breaker:**
```python
# Every service gets a shared httpx client with timeouts
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(connect=2.0, read=10.0, write=5.0, pool=1.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)
```

---

## 5. Event Streaming Layer (Kafka)

### 5.1 Cluster Configuration

Using **Confluent Cloud** (managed Kafka) for production:
- **3 brokers** across 3 availability zones.
- **Replication factor: 3** for all critical topics.
- **min.insync.replicas: 2** — a write is only confirmed if 2 replicas acknowledge it.
- **acks=all** on producers — no message loss on broker failure.

### 5.2 Topic Design

```
Topic Name              | Partitions | Retention | Replication
------------------------|------------|-----------|------------
build.queued            | 12         | 7 days    | 3
build.logs.{deploy_id}  | 1          | 24 hours  | 2
build.completed         | 12         | 7 days    | 3
build.failed            | 12         | 7 days    | 3
deployment.uploaded     | 12         | 7 days    | 3
deployment.live         | 12         | 7 days    | 3
deployment.rollback     | 12         | 7 days    | 3
dead.letter.queue       | 12         | 30 days   | 3
```

**Partition key strategy:** Always use `project_id` as the partition key. This guarantees that all events for the same project arrive in-order to the same partition — critical for correct state transitions (queued → building → live).

### 5.3 Consumer Group Design

```
Clients (Web, CLI)
        ↓
    APISIX Gateway
        ↓
``` | Instances | Lag Alert Threshold
------------------------|----------------|-----------|--------------------
build-orchestrator-cg   | build.queued   | 3         | >100 messages
upload-service-cg       | build.completed| 2         | >50 messages
deployment-service-cg   | deployment.*   | 2         | >50 messages
ai-service-cg           | build.failed   | 1         | >200 messages
log-archiver-cg         | build.logs.*   | 2         | >1000 messages
```

### 5.4 Producer Configuration (No Message Loss)

```python
producer_config = {
    "acks": "all",                    # wait for all ISR replicas
    "retries": 10,
    "retry.backoff.ms": 100,
    "max.in.flight.requests.per.connection": 1,  # preserve ordering
    "enable.idempotence": True,       # exactly-once producer semantics
    "compression.type": "lz4",       # reduce network overhead
    "batch.size": 65536,             # 64KB batches
    "linger.ms": 5,                  # wait up to 5ms to fill batch
}
```

### 5.5 Dead Letter Queue (DLQ)

Every consumer implements DLQ logic:
```python
async def consume_with_dlq(consumer, process_fn, max_retries=3):
    async for message in consumer:
        retry_count = message.headers.get("retry-count", 0)
        try:
            await process_fn(message)
            await consumer.commit()
        except RetryableError as e:
            if retry_count < max_retries:
                await producer.send(
                    message.topic,
                    value=message.value,
                    headers={"retry-count": str(retry_count + 1)},
                )
            else:
                await producer.send("dead.letter.queue", value={
                    "original_topic": message.topic,
                    "payload": message.value,
                    "error": str(e),
                    "timestamp": utcnow(),
                })
```

---

## 6. Data Layer

### 6.1 PostgreSQL (via Neon.tech)

Neon provides **serverless Postgres** with:
- **Autoscaling compute** — scales from 0.25 vCPU to 7 vCPU instantly.
- **Branching** — instant read-only branches for staging, testing.
- **Point-in-time recovery** — restore to any second in the last 7 days.
- **Connection pooling via PgBouncer** — handles thousands of connections.

**Connection pool sizing per pod:**
```
pool_size = (CPU cores × 2) + 1 = 5 connections per pod
max_overflow = 5 (burst)
Total per service = pods × 10 connections
Auth (2 pods) = 20 connections to Neon
```

### 6.2 Database Schema Optimizations

```sql
-- Critical indexes for hot query paths
CREATE INDEX CONCURRENTLY idx_projects_user_id 
    ON projects(user_id) WHERE status = 'active';

CREATE INDEX CONCURRENTLY idx_deployments_project_status 
    ON deployments(project_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY idx_build_logs_run_id 
    ON build_logs(build_run_id, line_number);

-- Partition build_logs by month (high write volume)
CREATE TABLE build_logs (
    id UUID DEFAULT gen_random_uuid(),
    build_run_id UUID NOT NULL,
    log_line TEXT NOT NULL,
    line_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE build_logs_2024_01 PARTITION OF build_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Row-level locking for deployment state machine
UPDATE deployments 
SET status = 'building' 
WHERE id = $1 AND status = 'queued'  -- atomic state transition
RETURNING id;
```

### 6.3 Optimistic Concurrency Control

Prevent race conditions on concurrent updates:
```sql
ALTER TABLE deployments ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

-- Update with version check (concurrent update will fail)
UPDATE deployments
SET status = 'live', version = version + 1, deployed_at = NOW()
WHERE id = $1 AND version = $2;  -- $2 = expected version from application
-- If 0 rows updated, someone else modified it first → retry
```

---

## 7. Caching Strategy (Redis)

Using **Upstash Redis** (managed, serverless, global replicas):

### 7.1 Cache Layers

| Data | TTL | Invalidation Strategy |
|---|---|---|
| JWT blacklist (logout) | 15 min (token lifetime) | Write-on-logout |
| User profile (`/auth/me`) | 5 min | Event-driven invalidation |
| Project list per user | 2 min | Invalidated on project CUD |
| Active deployment status | 30 sec | Pub/Sub on status change |
| GitHub API responses | 60 sec | TTL-based |
| Build locks | 15 min + TTL | Released on build complete |
| Rate limit counters | Sliding window | Auto-expiry |

### 7.2 Distributed Lock for Build Slots

```python
# Prevent multiple builds running simultaneously for same project
class BuildLock:
    def __init__(self, redis: Redis, project_id: str):
        self.lock = redis.lock(
            f"build:lock:{project_id}",
            timeout=600,        # 10 min max build time
            blocking_timeout=5, # wait max 5s to acquire
        )

    async def __aenter__(self):
        if not await self.lock.acquire():
            raise BuildAlreadyRunning("A build is already in progress")
        return self

    async def __aexit__(self, *args):
        await self.lock.release()
```

### 7.3 Redis Pub/Sub for Deployment Status

```python
# Deployment service publishes on status change
await redis.publish(
    f"deployment:status:{deployment_id}",
    json.dumps({"status": "live", "url": deployment_url})
)

# Centrifugo bridges Redis Pub/Sub → WebSocket to browser
# (configured natively via Centrifugo's Redis engine)
```

---

## 8. Build Orchestration at Scale

This is the most complex and resource-intensive service. It needs special treatment.

### 8.1 Build Slot Management

```
Available build slots = Kafka partition count for build.queued = 12
Build Orchestrator pods = 3 (each handles 4 partitions)
Max concurrent builds system-wide = 12 (limited by Kafka partitions)
```

Scale by increasing Kafka partitions + adding pods.

### 8.2 Docker Build Isolation

```
Each build gets:
  - Unique Docker network namespace
  - Resource limits: 512MB RAM, 1 CPU, 10-min timeout
  - Ephemeral volume (tmpfs) — no disk persistence
  - No network access (except git clone at start)
  - Read-only filesystem except /build output dir
  - Non-root user inside container
  - seccomp profile to restrict syscalls
```

```python
docker_run_config = {
    "image": "node:20-alpine",
    "command": ["sh", "-c", build_script],
    "mem_limit": "512m",
    "cpu_quota": 100000,       # 1 CPU
    "network_mode": "none",    # no network after git clone
    "read_only": True,
    "tmpfs": {"/tmp": "size=200m"},
    "volumes": {build_output_dir: {"bind": "/output", "mode": "rw"}},
    "user": "1000:1000",
    "security_opt": ["no-new-privileges:true"],
    "auto_remove": True,
}
```

### 8.3 Log Streaming Architecture

```
Docker container stdout/stderr
        │ docker.attach() stream
        ▼
Build Orchestrator Python process
        │ async generator, line by line
        ▼
Kafka producer → topic: build.logs.{deployment_id}
        │
        ├── Log Archiver Consumer → PostgreSQL build_logs table
        │
        └── Centrifugo Consumer → WebSocket → Browser
```

```python
# Async log streaming from Docker container to Kafka
async def stream_build_logs(container, deployment_id: str, producer):
    line_number = 0
    async for log_chunk in container.log_stream():
        for line in log_chunk.decode().splitlines():
            line_number += 1
            await producer.send(
                f"build.logs.{deployment_id}",
                value={"line": line, "line_number": line_number, "ts": utcnow()}
            )
```

### 8.4 Horizontal Pod Autoscaler for Build Orchestrator

```yaml
# HPA scales Build Orchestrator based on Kafka consumer lag
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: build-orchestrator-scaler
spec:
  scaleTargetRef:
    name: build-orchestrator
  minReplicaCount: 2
  maxReplicaCount: 20      # up to 20 pods during traffic spike
  triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka.confluent.cloud:9092
      consumerGroup: build-orchestrator-cg
      topic: build.queued
      lagThreshold: "5"    # scale up if >5 messages per pod
```

---

## 9. Real-Time Layer (WebSocket)

### 9.1 Centrifugo (WebSocket Broker)

Centrifugo handles all WebSocket connections between clients and the event system:

```
Browser → WebSocket → Centrifugo → Redis Pub/Sub ← Microservices
```

- **2 replicas** with shared Redis state — any pod can handle any client.
- Supports **100k+ concurrent connections** per node.
- Clients subscribe to named **channels** (not topics):
  - `deployment:{id}:status` — deployment state changes
  - `build:{id}:logs` — real-time log lines
  - `project:{id}:activity` — any activity on a project

```javascript
// Frontend subscribes to build logs channel
const sub = centrifuge.newSubscription(`build:${deploymentId}:logs`);
sub.on('publication', (ctx) => {
  appendLogLine(ctx.data.line);
});
sub.subscribe();
```

### 9.2 WebSocket Connection Resilience

- **JWT auth** on WebSocket connection (centrifugo validates on connect).
- **Reconnect with exponential backoff** — client retries with full message replay on reconnect.
- **Offset tracking** — Centrifugo replays missed messages using sequence numbers.
- **Presence** — optional: see who's watching a deployment.

---

## 10. Concurrency & Distributed Locking

### 10.1 Key Concurrency Problems Solved

| Problem | Solution |
|---|---|
| Two builds triggered simultaneously for same project | Redis distributed lock (`build:lock:{project_id}`) |
| Webhook delivered twice (GitHub retry) | Idempotency key: `X-GitHub-Delivery` header → check Redis before processing |
| Deployment state machine race | Postgres optimistic locking (`WHERE status = 'expected_status'`) |
| Multiple pods consuming same Kafka message | Kafka consumer group guarantees exactly-one delivery per group |
| Concurrent env var reads/writes | DB row-level locking + encrypted at rest |
| Duplicate S3 uploads | S3 key is deterministic (`deployments/{project_id}/{deployment_id}/`) — idempotent upload |

### 10.2 Idempotency Keys

Every mutating API endpoint accepts an `Idempotency-Key` header:

```python
@app.post("/projects/{id}/deployments")
async def trigger_deployment(
    id: str,
    idempotency_key: str = Header(None),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if idempotency_key:
        cached = await redis.get(f"idempotency:{idempotency_key}")
        if cached:
            return JSONResponse(json.loads(cached))  # return cached response

    result = await deployment_service.trigger(id)
    
    if idempotency_key:
        await redis.setex(
            f"idempotency:{idempotency_key}",
            86400,  # 24 hours
            json.dumps(result)
        )
    return result
```

### 10.3 Saga Pattern for Multi-Step Deployments

The deployment pipeline is a distributed transaction across 4 services. We use a **Choreography Saga**:

```
Step 1: Project Service  → publishes build.queued
Step 2: Build Orchestrator → publishes build.completed | build.failed
Step 3: Upload Service   → publishes deployment.uploaded
Step 4: Deployment Service → publishes deployment.live

Compensating transactions (on failure):
  - build.failed      → mark deployment as failed, notify user
  - upload failure    → delete partial S3 upload, mark failed
  - routing failure   → revert Caddy config, mark failed
```

---

## 11. Resilience Patterns

### 11.1 Circuit Breaker

Applied on all outbound calls (GitHub API, S3, Caddy, AI Service):

```python
from circuitbreaker import circuit

@circuit(
    failure_threshold=5,      # open after 5 failures
    recovery_timeout=30,      # try again after 30 seconds
    expected_exception=httpx.RequestError,
)
async def call_github_api(endpoint: str, **kwargs):
    return await http_client.get(f"https://api.github.com{endpoint}", **kwargs)
```

States: `CLOSED` (normal) → `OPEN` (fail fast) → `HALF-OPEN` (probe) → `CLOSED`

### 11.2 Retry with Exponential Backoff

```python
from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log
)

@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def upload_to_s3(path: str, bucket: str, key: str):
    ...
```

### 11.3 Bulkhead Pattern

Each service type gets its own connection pool — one service's overload doesn't starve others:

```python
# Separate thread pools / semaphores per external dependency
github_semaphore = asyncio.Semaphore(20)   # max 20 concurrent GitHub calls
s3_semaphore = asyncio.Semaphore(50)       # max 50 concurrent S3 ops
caddy_semaphore = asyncio.Semaphore(10)    # max 10 concurrent Caddy API calls
ai_semaphore = asyncio.Semaphore(5)        # max 5 concurrent OpenAI calls
```

### 11.4 Health Check Endpoints

Every service exposes:

```python
@app.get("/health")   # liveness: is the process alive?
async def health():
    return {"status": "ok"}

@app.get("/ready")    # readiness: can it handle traffic?
async def ready(db=Depends(get_db), redis=Depends(get_redis)):
    await db.execute(text("SELECT 1"))
    await redis.ping()
    return {"status": "ready", "db": "ok", "redis": "ok"}
```

Kubernetes uses `/health` for liveness and `/ready` for readiness probes.

### 11.5 Graceful Shutdown

```python
@app.on_event("shutdown")
async def shutdown():
    # Stop accepting new requests
    # Finish in-flight requests (30s grace period)
    await kafka_consumer.stop()
    await kafka_producer.stop()
    await db_engine.dispose()
    await redis.close()
```

---

## 12. Observability Stack

### 12.1 The Three Pillars

```
Metrics  → Prometheus + Grafana    (what is happening)
Logs     → Loki / Cloud Logging    (what happened)
Traces   → Tempo / Jaeger          (why did it happen)
```

### 12.2 Distributed Tracing (OpenTelemetry)

Every request gets a `trace_id` that flows through all services and Kafka messages:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Auto-instruments FastAPI, SQLAlchemy, and httpx
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
```

Trace propagated via Kafka headers:
```python
# Producer: inject trace context into Kafka headers
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("publish_build_queued"):
    carrier = {}
    TraceContextTextMapPropagator().inject(carrier)
    await producer.send(topic, headers=carrier, value=payload)

# Consumer: extract trace context from Kafka headers
ctx = TraceContextTextMapPropagator().extract(message.headers)
with tracer.start_as_current_span("consume_build_queued", context=ctx):
    await process(message)
```

### 12.3 Key Metrics to Monitor

```
# SLIs (Service Level Indicators)
http_request_duration_seconds     (p50, p95, p99 per route)
http_requests_total               (by status code)
kafka_consumer_lag                (per consumer group, per topic)
build_duration_seconds            (p50, p95, p99)
deployment_success_rate           (builds that reach "live")
db_query_duration_seconds         (p95 per query)

# Alerts
- API error rate > 1% for 5 min  → PagerDuty
- Kafka consumer lag > 1000      → PagerDuty  
- Build failure rate > 10%       → Slack
- Pod OOMKilled                  → PagerDuty
- Redis memory > 80%             → Slack
```

---

## 13. Infrastructure Topology (GKE)

### 13.1 Cluster Layout

```
GKE Cluster: deployhub-prod
  Region: us-central1
  Node Pools:
  
  ┌─────────────────────────────┐
  │ general-pool                │  ← All stateless services
  │ Machine: e2-standard-4      │
  │ Nodes: 3-10 (autoscaled)    │
  │ Preemptible: No             │
  └─────────────────────────────┘
  
  ┌─────────────────────────────┐
  │ build-pool                  │  ← Build Orchestrator pods only
  │ Machine: c2-standard-8      │  ← High CPU for Docker builds
  │ Nodes: 2-8 (autoscaled)     │
  │ Preemptible: Yes (saves 70%)│  ← Builds are fault-tolerant
  │ Taints: workload=builds     │
  └─────────────────────────────┘
```

### 13.2 Kubernetes Resource Manifests (Pattern)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0        # zero-downtime deploys
      maxSurge: 1
  template:
    spec:
      containers:
      - name: auth-service
        image: gcr.io/deployhub/auth-service:latest
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet: { path: /health, port: 8000 }
          periodSeconds: 10
        readinessProbe:
          httpGet: { path: /ready, port: 8000 }
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef: { name: db-secret, key: url }
      affinity:
        podAntiAffinity:       # spread pods across nodes
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels: { app: auth-service }
            topologyKey: kubernetes.io/hostname
```

### 13.3 Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: auth-service-pdb
spec:
  minAvailable: 1          # always 1 pod running during node upgrades
  selector:
    matchLabels: { app: auth-service }
```

---

## 14. Security Architecture

### 14.1 Secrets Management

- All secrets in **GCP Secret Manager** (not environment variables, not Kubernetes Secrets).
- Pods use Workload Identity to fetch secrets at startup.
- Environment variables are encrypted with **AES-256-GCM** before DB write.
- Encryption key stored in Secret Manager, never in code.

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_env_var(value: str, key: bytes) -> str:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()
```

### 14.2 mTLS Between Services (Service Mesh)

With **Istio** or **Linkerd**:
- All service-to-service traffic is **mutually authenticated TLS**.
- A compromised pod cannot impersonate another service.
- Network policies restrict which services can talk to which.

### 14.3 JWT Security

```
Access Token:  RS256, 15-minute expiry, stored in memory (not localStorage)
Refresh Token: RS256, 7-day expiry, HttpOnly + Secure + SameSite=Strict cookie
Rotation:      Refresh token rotated on each use (refresh token rotation)
Revocation:    Access token hash in Redis blacklist on logout
```

---

## 15. Data Flow: Critical Paths

### Path 1: GitHub Webhook → Live Deployment (Happy Path)

```
T+0ms   : GitHub POST /webhook/github/{project_id}
T+5ms   : HMAC validated, build.queued published to Kafka
T+10ms  : HTTP 200 returned to GitHub

T+500ms : Build Orchestrator consumes build.queued
T+1s    : Docker container spins up, git clone begins
T+3s    : First log line published to Kafka → visible in browser
T+3min  : Build completes, build.completed published
T+4min  : Upload Service uploads artifacts to S3
T+4.5min: Deployment Service updates Caddy routing
T+4.6min: deployment.live published → Browser shows "Deployed ✓"
T+4.7min: User can open live URL
```

### Path 2: Deployment Rollback

```
T+0s    : User clicks "Rollback to #5" in dashboard
T+100ms : POST /deployments/{id}/rollback received
T+200ms : Deployment Service reads previous S3 path from DB
T+300ms : Caddy config updated to point to previous S3 path
T+400ms : Deployment #6 status = rolled_back, Deployment #5 status = live
T+500ms : deployment.live event published, browser updates
```

---

## 16. Scaling Runbook

### Load Targets & Scaling Thresholds

| Load Level | Active Builds | API Req/s | Kafka Lag | Action |
|---|---|---|---|---|
| Baseline | 0-3 | < 50 | < 10 | 2 pods each service |
| Normal | 4-10 | 50-200 | < 50 | HPA adds pods |
| High | 11-20 | 200-500 | < 200 | Build pool scales out |
| Spike | 21-50 | 500-2000 | < 500 | All pools max scale |
| Saturation | >50 | >2000 | >500 | Queue builds, shed load |

### Vertical Scaling Path

When a single build takes > 512MB RAM (large monorepos):
- Build Orchestrator detects OOM during resource limit check.
- Publishes `build.config.heavy` event.
- Relaunches Docker container with 2GB limit on dedicated heavy-build node pool.

---

## Summary: Why This Architecture is Fail-Proof

| Risk | How We Handle It |
|---|---|
| Service crash | Kubernetes restarts pod, min 2 replicas, zero-downtime |
| DB failure | Neon managed HA, auto-failover in < 30s |
| Kafka broker down | 3 brokers, 2 broker minimum for writes, auto-rebalance |
| Redis failure | Upstash managed, cluster mode, replica failover |
| S3 unavailable | S3 has 99.999999999% durability, multi-AZ by default |
| Build node crash | Build re-queued, Kafka offset not committed → automatic retry |
| DDoS | Cloudflare absorbs attack at edge |
| Memory leak | OOMKilled by Kubernetes, pod restarted fresh |
| Stuck build | 10-minute timeout kills Docker container, marks deployment failed |
| Race condition | Distributed lock + DB optimistic locking |
| Duplicate message | Idempotency keys + Kafka exactly-once semantics |
| Rolling deploy downtime | maxUnavailable=0, graceful shutdown, drain period |
