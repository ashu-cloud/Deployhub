# DeployHub — Architecture & Microservices Flow Diagram

This document illustrates the complete architectural topology and runtime interaction flow of DeployHub, covering the Next.js frontend application, API routing, all 5 core FastAPI microservices, asynchronous Kafka event streaming, and Caddy reverse-proxying.

---

## 1. High-Level Architecture & Traffic Topology

```mermaid
graph TB
    subgraph Clients["Clients & External Triggers"]
        Dev["Developer / Browser (Next.js SPA)"]
        GH["GitHub (Push / Webhook Events)"]
        UserTraffic["End-User Web Traffic (Custom Domains / Subdomains)"]
    end

    subgraph EdgeLayer["Edge & Gateway Routing"]
        NextProxy["Next.js Gateway Rewrites / APISIX Ingress<br/>(:3000 / :80)"]
        CaddyProxy["Caddy Edge Reverse Proxy<br/>(:80, :443)"]
    end

    subgraph CoreServices["DeployHub Microservices Layer"]
        AuthSvc["Auth Service (:8001)<br/>• GitHub OAuth<br/>• RS256 JWT Issuance<br/>• Refresh Token Rotation"]
        ProjSvc["Project Service (:8002)<br/>• Projects CRUD & Domains<br/>• AES-256 Encrypted Env Vars<br/>• GitHub Webhook Receiver"]
        BuildSvc["Build Orchestrator (:8004)<br/>• Docker Sandbox Builder<br/>• Redis Distributed Lock<br/>• Live Log Streamer<br/>• Groq AI Error Diagnoser"]
        UploadSvc["Upload Service (:8005)<br/>• Artifact Extractor<br/>• S3 / MinIO Uploader<br/>• Cleanup Worker"]
        DeploySvc["Deployment Service (:8006)<br/>• Caddy Unix Socket Router<br/>• Instant Rollback Engine<br/>• WebSocket Log Streamer (:ws)"]
    end

    subgraph EventStream["Asynchronous Event Bus (Apache Kafka KRaft)"]
        Kafka["Kafka Event Topics<br/>• build.queued<br/>• build.completed<br/>• build.failed<br/>• deployment.uploaded<br/>• deployment.live"]
    end

    subgraph DataStorage["Data & State Persistence Layer"]
        Postgres[("PostgreSQL 15<br/>• Users & OAuth Tokens<br/>• Projects & Custom Domains<br/>• Deployments & Env Vars")]
        Redis[("Redis 7<br/>• Distributed Build Locks<br/>• Pub/Sub Real-time Channels<br/>• Rate Limiting & Cache")]
        MinIO[("MinIO / S3 Storage<br/>• Immutable Deployment Artifacts<br/>• /deployments/{proj}/{dep}/")]
        SharedVol["Shared Volume: deployhub_builds<br/>(/tmp/builds/{deployment_id})"]
    end

    %% Ingress connections
    Dev -->|"HTTP / REST API /auth, /projects"| NextProxy
    Dev -->|"WebSocket (Real-time Logs & Status)"| DeploySvc
    GH -->|"POST /api/v1/webhooks/github/{id}<br/>(HMAC SHA-256)"| NextProxy
    UserTraffic -->|"HTTP/HTTPS {project}.deployhub.dev"| CaddyProxy

    %% Gateway to services
    NextProxy -->|"Proxy /api/v1/auth/*"| AuthSvc
    NextProxy -->|"Proxy /api/v1/projects/*"| ProjSvc
    NextProxy -->|"Proxy /api/v1/webhooks/*"| ProjSvc
    NextProxy -->|"Proxy /api/v1/deployments/*"| DeploySvc

    %% Service Database access
    AuthSvc --> Postgres
    ProjSvc --> Postgres
    ProjSvc --> Redis
    DeploySvc --> Postgres
    DeploySvc --> Redis

    %% Kafka Events Flow
    ProjSvc -->|"1. Publish build.queued"| Kafka
    Kafka -->|"2. Consume build.queued"| BuildSvc
    BuildSvc -->|"3. Publish build.completed / build.failed"| Kafka
    Kafka -->|"4. Consume build.completed"| UploadSvc
    UploadSvc -->|"5. Publish deployment.uploaded"| Kafka
    Kafka -->|"6. Consume deployment.uploaded"| DeploySvc
    DeploySvc -->|"7. Publish deployment.live"| Kafka

    %% Build & Upload shared storage
    BuildSvc -->|"Write Artifacts & Clones"| SharedVol
    SharedVol -->|"Read Artifacts ('dist', 'out')"| UploadSvc
    UploadSvc -->|"Stream Objects"| MinIO
    BuildSvc --> Postgres
    BuildSvc -->|"Acquire build:lock:{project_id}"| Redis
    BuildSvc -->|"Publish build:{id}:logs & ai_diagnosis"| Redis

    %% Dynamic Routing & Serving
    DeploySvc -->|"Dynamic config via Unix Socket (/srv/caddy-admin)"| CaddyProxy
    CaddyProxy -->|"Reverse Proxy traffic to S3 bucket assets"| MinIO
```

---

## 2. End-to-End Build & Deployment Flow (Choreographed Saga)

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer / GitHub
    participant Frontend as Next.js Dashboard
    participant ProjSvc as Project Service (:8002)
    participant Kafka as Apache Kafka (KRaft)
    participant BuildSvc as Build Orchestrator (:8004)
    participant Docker as Isolated Docker Container
    participant Redis as Redis (Pub/Sub & Locks)
    participant UploadSvc as Upload Service (:8005)
    participant S3 as MinIO / AWS S3
    participant DeploySvc as Deployment Service (:8006)
    participant Caddy as Caddy Reverse Proxy
    participant DB as PostgreSQL 15

    %% Triggering Phase
    Note over Dev, ProjSvc: Phase 1: Trigger & Ingress (< 15ms)
    alt Git Push (Webhook)
        Dev->>ProjSvc: POST /webhooks/github/{id} (Payload + HMAC signature)
        ProjSvc->>ProjSvc: Validate X-Hub-Signature-256 HMAC
    else Manual Trigger
        Frontend->>ProjSvc: POST /projects/{id}/deploy?branch=main (Bearer JWT)
    end
    ProjSvc->>DB: INSERT INTO deployments (status='queued')
    ProjSvc->>Kafka: Publish "build.queued" (Key = project_id)
    ProjSvc-->>Dev: HTTP 200 OK {"status": "queued"}

    %% Build Phase
    Note over Kafka, Redis: Phase 2: Build Orchestration & Sandboxing
    Kafka->>BuildSvc: Consume "build.queued"
    BuildSvc->>Redis: Acquire Distributed Lock "build:lock:{project_id}"
    BuildSvc->>DB: UPDATE deployments SET status='building'
    BuildSvc->>BuildSvc: Git clone repository into /tmp/builds/{dep_id}
    BuildSvc->>DB: SELECT encrypted environment variables
    BuildSvc->>BuildSvc: Decrypt env vars using AES-256-GCM
    BuildSvc->>Docker: Run container (512MB RAM, 1 CPU, non-root, read-only root)

    %% Real-time log streaming
    par Real-Time Log Streaming
        loop stdout/stderr line streaming
            Docker->>BuildSvc: Docker log stream chunk
            BuildSvc->>Redis: PUBLISH "build:{deployment_id}:logs" {"line": "..."}
            Redis->>DeploySvc: PubSub receive log line
            DeploySvc->>Frontend: WebSocket Push {"line": "..."}
        end
    and Container Build Execution
        Docker->>Docker: npm install && npm run build
    end

    %% Build Outcome
    alt Build Succeeded
        Docker-->>BuildSvc: Exit Code 0 (Artifacts generated in dist/out)
        BuildSvc->>Kafka: Publish "build.completed" (Key = project_id)
        BuildSvc->>Redis: Release Distributed Lock
    else Build Failed
        Docker-->>BuildSvc: Exit Code != 0
        BuildSvc->>DB: UPDATE deployments SET status='failed'
        BuildSvc->>BuildSvc: Trigger AI Diagnoser (Groq LLM)
        BuildSvc->>Redis: PUBLISH "build:{deployment_id}:ai_diagnosis"
        Redis->>DeploySvc: Forward AI Diagnosis
        DeploySvc->>Frontend: WebSocket Push {"ai_token": "..."}
        BuildSvc->>Kafka: Publish "build.failed"
        BuildSvc->>Redis: Release Distributed Lock
    end

    %% Upload Phase
    Note over Kafka, S3: Phase 3: Artifact Upload & Packaging
    Kafka->>UploadSvc: Consume "build.completed"
    UploadSvc->>DB: UPDATE deployments SET status='uploading'
    UploadSvc->>S3: Recursively upload /tmp/builds/{dep_id}/dist -> deployments/{proj}/{dep}/
    UploadSvc->>DB: UPDATE deployments SET status='uploaded', s3_path='...'
    UploadSvc->>UploadSvc: Delete /tmp/builds/{dep_id} from shared volume
    UploadSvc->>Kafka: Publish "deployment.uploaded" (Key = project_id)

    %% Deployment Go-Live Phase
    Note over Kafka, Caddy: Phase 4: Dynamic Routing & Go-Live (< 100ms)
    Kafka->>DeploySvc: Consume "deployment.uploaded"
    DeploySvc->>DB: Fetch project subdomain & verified custom domains
    DeploySvc->>Caddy: Dynamic Route Update via Unix Socket (/srv/caddy-admin/admin.sock)
    Note over Caddy: Caddy matches host {subdomain}.localhost,<br/>rewrites / -> /index.html,<br/>proxies to MinIO:9000/{bucket}/{s3_path}/
    DeploySvc->>DB: UPDATE deployments SET status='live', deployed_at=NOW()
    DeploySvc->>Kafka: Publish "deployment.live"
    DeploySvc->>Redis: PUBLISH "deployment:{deployment_id}:status" {"status": "live", "url": "..."}
    Redis->>DeploySvc: Forward status update
    DeploySvc->>Frontend: WebSocket Push {"status": "live", "url": "..."}
    Frontend->>Frontend: UI displays green checkmark & live URL button!
```

---

## 3. Instant Rollback Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / Operator
    participant UI as Next.js Dashboard
    participant DeploySvc as Deployment Service (:8006)
    participant DB as PostgreSQL 15
    participant Caddy as Caddy Proxy (Unix Socket)
    participant Redis as Redis Pub/Sub

    User->>UI: Clicks "Rollback to Deployment #3"
    UI->>DeploySvc: POST /api/v1/deployments/{id}/rollback (Bearer JWT)
    DeploySvc->>DB: Query Deployment #3 (verify status='live' or previous successful deployment)
    DeploySvc->>DB: Retrieve s3_path = "deployments/{project_id}/{deployment_id_3}"
    DeploySvc->>Caddy: PATCH /config/apps/http/servers/srv0/routes (via Unix Socket)
    Note over Caddy: Caddy updates host reverse proxy upstream path<br/>from Deployment #5 to Deployment #3 instantaneously (<5ms)
    DeploySvc->>DB: Mark Deployment #3 as 'live', previous deployment as 'rolled_back'
    DeploySvc->>Redis: PUBLISH deployment status update
    DeploySvc-->>UI: HTTP 200 {"message": "Rollback successful", "live_url": "http://..."}
    UI-->>User: Instant notification "Active deployment reverted to #3" (< 300ms total)
```
