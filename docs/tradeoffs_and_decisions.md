# Tradeoffs and Design Decisions

This document explains the "Why" behind the architectural choices in DeployHub. Building a distributed system requires balancing performance, development speed, operational complexity, and cost. 

If you are an engineer or a recruiter reading this, this document serves as a masterclass on the systemic thinking applied to this project.

---

## 1. FastAPI (Python) vs. Express/NestJS (Node.js) vs. Go

DeployHub's microservices are written in Python using FastAPI.

### Why FastAPI?
- **Asynchronous I/O Support:** FastAPI natively supports `asyncio`, which is critical for a platform where services spend 90% of their time waiting on network I/O (Database queries, Kafka publishing, GitHub API calls, Docker build orchestration).
- **Pydantic Validation:** The tight integration with Pydantic means request payloads and Kafka event schemas are strictly validated at the boundaries, preventing malformed data from poisoning the event stream.
- **Developer Velocity:** Python's readability and massive ecosystem allowed for rapid MVP iteration.

### Pros:
- Excellent auto-generated OpenAPI documentation.
- Very fast relative to traditional Python frameworks (Django/Flask) due to ASGI and Starlette.
- Strict typing (via Pydantic) catches bugs early.

### Cons & Tradeoffs:
- **CPU Bound Limitations:** The Python Global Interpreter Lock (GIL) means true multithreading for CPU-bound tasks is limited. 
- **Memory Footprint:** Python processes consume more memory than a compiled language like Go.

### Why not Go?
Go is the industry standard for cloud-native infrastructure (Kubernetes, Docker, Terraform). While Go would have resulted in smaller binaries and lower memory usage, it would have slowed down the initial development speed for the MVP. In a future iteration, the `Build Orchestrator` service (which is the most resource-intensive) would be a prime candidate to be rewritten in Go.

---

## 2. Apache Kafka vs. RabbitMQ vs. Redis Pub/Sub

The backbone of DeployHub is an event-driven architecture using Apache Kafka (hosted on Confluent Cloud).

### Why Kafka?
- **Event Replayability (Retention):** Unlike RabbitMQ or Redis, Kafka stores events on disk for a configured retention period (e.g., 7 days). If a microservice crashes and is offline for an hour, it can spin back up and consume the events it missed exactly from where it left off.
- **Partitioning for Concurrency:** By partitioning topics using `project_id`, we guarantee that all events for a specific project are processed *in order* by the exact same consumer pod. This is crucial for state transitions (queued -> building -> live).
- **Scale out:** We can easily scale the Build Orchestrator by simply adding more pods up to the number of Kafka partitions.

### Pros:
- Massive throughput capability.
- High durability and fault tolerance (acks=all).
- Decouples services (Project Service doesn't know about Build Orchestrator).

### Cons & Tradeoffs:
- **Operational Complexity:** Kafka is notoriously complex to run and configure correctly. We mitigated this by using a managed service (Confluent Cloud).
- **Latency:** Kafka has slightly higher latency than a purely in-memory queue like Redis.

### Why not Redis Pub/Sub?
Redis Pub/Sub is "fire and forget". If a consumer is disconnected when a message is published, that message is gone forever. This is unacceptable for a build pipeline where missing a `build.queued` event means a user's deployment never happens. 

---

## 3. Serverless PostgreSQL (Neon) vs. MongoDB vs. Traditional RDS

For the primary data store, DeployHub uses PostgreSQL hosted on Neon.tech.

### Why PostgreSQL?
- **ACID Compliance & State Machines:** Deployments are complex state machines. We need strict ACID transactions to ensure that two concurrent webhooks don't trigger two builds simultaneously. We use row-level locking (`UPDATE ... WHERE status = 'queued'`) to ensure atomic transitions.
- **Relational Data:** Users have Projects, Projects have Deployments, Deployments have Build Logs. This is highly relational data.

### Why Neon (Serverless)?
- **Scale to Zero & Instant Compute:** The database automatically scales compute resources based on load. 
- **Branching:** Neon allows creating instant read/write branches of the database (like Git branches), which made testing staging environments incredibly easy and isolated.

### Pros:
- Zero operational overhead for scaling the DB.
- Strict data integrity via foreign keys and constraints.

### Cons & Tradeoffs:
- Connection limits: Serverless databases can quickly run out of connections if you have hundreds of microservice pods. We mitigated this by using PgBouncer for connection pooling and keeping the pool size small per pod.

### Why not MongoDB?
A NoSQL database would make it harder to enforce the strict relational constraints (e.g., deleting a project should cascade delete all its deployments). Furthermore, the transaction support in Postgres is much more robust for our state transitions.

---

## 4. Centrifugo + Redis for Real-Time Logs

When a build is running, logs stream to the frontend in real-time. This is handled by Centrifugo acting as a WebSocket broker.

### Why Centrifugo?
- **Massive Connection Scaling:** It is written in Go and designed specifically to hold hundreds of thousands of concurrent WebSocket connections efficiently.
- **Built-in Redis Engine:** Our microservices don't need to hold WebSocket connections. They simply publish a message to Redis (`redis.publish(channel, message)`), and Centrifugo automatically fans it out to all browsers subscribed to that channel.
- **Connection Recovery:** Centrifugo maintains a short history buffer. If a user's internet drops for 5 seconds, when they reconnect, Centrifugo automatically replays the missed log lines.

### Pros:
- Offloads stateful connection management from our stateless Python backend.
- Trivially scalable just by adding more Centrifugo pods.

### Cons & Tradeoffs:
- Adds an extra infrastructure component to manage.

### Why not standard FastAPI WebSockets?
If a user is connected to Pod A via WebSocket, and the build logs are being processed by Pod B, Pod B has no way to send the logs directly to the user without a Pub/Sub layer in between. Moving the WebSocket handling entirely out of the Python layer prevents our API servers from being bogged down by idle, long-lived connections.

---

## 5. Docker Namespace Isolation for Builds

When a user pushes code, we run a Docker container to build it.

### The Decision:
Running untrusted user code is inherently dangerous. We isolate the build step:
- **No Network Access:** After the initial `git clone` and `npm install`, the network is disabled for the container (`network_mode: none`).
- **Resource Limits:** Hard limits on CPU (1 core) and Memory (512MB) prevent a malicious user from mining crypto or bringing down the build node.
- **Read-Only Filesystem:** The container cannot write anywhere except a specific temporary output directory.

### Tradeoff:
This extreme isolation means users cannot run builds that require fetching external resources *during* the build step (unless we pre-fetch or explicitly allow specific domains). However, the security benefits far outweigh the inconvenience, preventing container escape attacks and resource exhaustion.

---

## 6. Monorepo vs. Polyrepo

The project is structured as a **Monorepo** containing the frontend, all microservices, and infrastructure code.

### Why Monorepo?
- **Single Source of Truth:** Easy to search across the entire codebase.
- **Shared Code:** Microservices can share Pydantic schemas, database models, and core utilities (located in the `shared/` directory) without needing to publish private PyPI packages.
- **Atomic Commits:** A feature that requires a frontend change and a backend change can be deployed in a single PR.

### Cons & Tradeoffs:
- CI pipelines become more complex, as they need to detect *which* services changed to avoid rebuilding everything.
- Cloning the repo takes longer as the project grows.
