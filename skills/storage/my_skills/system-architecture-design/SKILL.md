---
name: "system-architecture-design"
description: "Master engineering blueprint for macro-level system architecture design, capacity estimation, architectural paradigm evaluation, and selective service decomposition. Synthesizes canonical methodologies of Martin Fowler (In-Process Modular Monoliths & Strangler Fig), Sam Newman (Out-of-Process Service Decomposition & Internal RPC Interfaces), Alex Xu (Back-of-the-Envelope Capacity Estimation & Multi-Tier Topology), and Chris Richardson (Subdomain Decomposition & Polyglot Persistence) into an authoritative system design framework."
version: "1.0.0"
author: "Antigravity Engineering Core"
tags: ["system-design", "software-architecture", "modular-monolith", "service-decomposition", "capacity-planning", "martin-fowler", "sam-newman", "alex-xu", "chris-richardson", "internal-api", "grpc", "polyglot-persistence"]
trigger_patterns:
  - "system design"
  - "system architecture design"
  - "high level design"
  - "modular monolith architecture"
  - "service extraction"
  - "capacity estimation"
  - "back of the envelope calculation"
  - "macro architecture"
---

# Master System Architecture Design & Selective Decomposition Methodology

> *"Architecture is the decisions that you wish you could get right early in a project, but that are not necessarily easy to change later. A well-designed system prioritizes high-cohesion in-process modularity first, extracting out-of-process services only when concrete operational drivers demand it."*

---

## 1. Scope & Macro-Architecture Hierarchy

This skill provides the **Tier 1 Macro-Architecture Framework** for software systems engineering. It establishes the global blueprint of an application before individual service topologies or internal worker state machines are implemented.

### The 3-Tier Systems Engineering Suite:

```mermaid
flowchart TD
    subgraph Tier1["Tier 1: Global System Architecture (This Skill)"]
        T1["system-architecture-design"]
        T1 --> A1["Functional & Non-Functional Requirements (SLAs)"]
        T1 --> A2["Capacity & Traffic Estimation (Alex Xu Standard)"]
        T1 --> A3["Architectural Style: Modular Monolith vs Distributed"]
        T1 --> A4["Selective Service Decomposition Decision Matrix"]
    end

    subgraph Tier2["Tier 2: Distributed Inter-Service Fabric"]
        T2["system-microservices-design"]
        T2 --> B1["DDD Bounded Contexts & Pact Contracts"]
        T2 --> B2["Saga Orchestration & Outbox CDC"]
        T2 --> B3["Envoy Mesh, Ingress & Resiliency (Circuit Breaker)"]
    end

    subgraph Tier3["Tier 3: Sub-Atomic Component Lifecycle"]
        T3["system-lifecycle-design"]
        T3 --> C1["3-Way Differential State Reconciliation"]
        T3 --> C2["Sticky Resource Leasing & Free Pools"]
        T3 --> C3["State Machine: Ingested ➔ Active ➔ Drain ➔ Tombstone"]
        T3 --> C4["Transactional Multi-File Atomic Shadow Swap"]
    end

    Tier1 -- "When out-of-process services are extracted" --> Tier2
    Tier2 -- "When implementing individual service workers/pods" --> Tier3
    Tier1 -- "When implementing in-process modules/daemons" --> Tier3
```

---

## 2. Foundational Pillars of the Four Pioneers

Every high-level system architecture governed by this skill adheres to the empirical standards established by four foundational authorities:

```mermaid
quadrantChart
    title High-Level System Architecture Pillars
    x-axis "Analytical / Quantitative Planning" --> "Qualitative / Structural Design"
    y-axis "Runtime Infrastructure & Ingress" --> "Domain Boundaries & Modularity"
    quadrant-1 "Martin Fowler (In-Process Modular Monolith)"
    quadrant-2 "Sam Newman (Selective Service Decomposition)"
    quadrant-3 "Alex Xu (Capacity Estimation & Ingress Topology)"
    quadrant-4 "Chris Richardson (Subdomain Decomposition & Persistence)"
    "Alex Xu: Capacity & Ingress": [0.25, 0.30]
    "Chris Richardson: Subdomain Persistence": [0.75, 0.35]
    "Sam Newman: Extraction Drivers": [0.30, 0.80]
    "Martin Fowler: Modular Monolith": [0.80, 0.85]
```

### 1. Alex Xu — Quantitative Capacity Estimation & Multi-Tier Topology
- **Back-of-the-Envelope Estimation:** Quantitative analysis of Daily Active Users (DAU), Read-to-Write ratios, Queries Per Second (QPS), Network Bandwidth, and multi-year storage projections prior to selecting technologies.
- **Multi-Tier Edge Ingress:** Layer 4/Layer 7 load balancing, GeoDNS routing, CDN caching for static and dynamic assets, and unified API Gateway rate limiting.

### 2. Martin Fowler — Componentization & In-Process Modularity
- **Modular Monolith Priority:** Software is divided into logically distinct, high-cohesion, low-coupling modules running inside a single process boundary.
- **Encapsulated In-Process Boundaries:** Modules expose public interface contracts (Facades) and communicate in-memory. Cross-module direct table queries or private class mutations are strictly forbidden.
- **Strangler Fig Pattern:** Evolutionary migration strategy that intercepts calls to legacy boundaries and routes them to new modules or extracted services without total system rewrites.

### 3. Sam Newman — Selective Service Decomposition
- **Operational Drivers for Extraction:** Services are not extracted based on code organization; they are extracted strictly when forced by operational variance (e.g., asymmetric scaling, compute heterogeneity, independent release cycles, fault isolation).
- **Internal Private RPC:** Extracted out-of-process services communicate with the core system over dedicated private networks using high-performance, strongly-typed internal RPC protocols (gRPC / HTTP/2 multiplexing) or asynchronous event streams.

### 4. Chris Richardson — Subdomain Decomposition & Polyglot Persistence
- **Domain-Driven Subdomain Classification:**
  - *Core Domain:* Primary competitive business logic.
  - *Supporting Subdomain:* Complements the core domain (e.g., inventory catalog, notification dispatch).
  - *Generic Subdomain:* Standardized industry workflows (e.g., identity, billing, analytics).
- **Polyglot Storage Strategy:** Selecting datastores strictly aligned with data access patterns (Relational RDBMS for transactional consistency, In-Memory Key-Value for low-latency caching, Columnar for analytical aggregation, Object Store for immutable blobs).

---

## 3. Quantitative Capacity Estimation Formulation (Alex Xu Standard)

Before producing structural diagrams, compute quantitative load metrics using the standard estimation pipeline:

```mermaid
flowchart LR
    DAU["1. User Demand\n(DAU / Concurrent Users)"] --> QPS["2. Throughput\n(Average & Peak QPS)"]
    QPS --> Bandwidth["3. Network\n(Ingress / Egress Gbps)"]
    QPS --> Storage["4. Persistence\n(Storage Growth / 5 Years)"]
    Storage --> Cache["5. In-Memory Sizing\n(80/20 Working Set RAM)"]
```

### Mathematical Formulation Matrix:

| Metric | Calculation Formula | Target Standard |
| :--- | :--- | :--- |
| **Average QPS** | $\text{QPS}_{\text{avg}} = \frac{\text{DAU} \times \text{Requests per User per Day}}{86,400\text{ seconds}}$ | Baseline operational traffic |
| **Peak QPS** | $\text{QPS}_{\text{peak}} = \text{QPS}_{\text{avg}} \times 2.0$ (or industry stress factor) | Infrastructure sizing boundary |
| **Read/Write Split** | Allocate based on domain profile (e.g., $90:10$ for Social/Content, $50:50$ for Financial/IoT) | Determines cache and replication strategy |
| **Network Egress** | $\text{Bandwidth} = \text{QPS}_{\text{peak}} \times \text{Average Payload Size}$ | Evaluates CDN offload and NIC constraints |
| **Storage (5 Years)** | $\text{Storage}_{\text{5yr}} = \text{Daily Writes} \times \text{Payload Size} \times 365 \times 5 \times 1.4$ (40% buffer for indexes/metadata) | Disk capacity & sharding threshold |
| **Memory Cache Size** | Apply Pareto Principle (80/20 Rule): Cache $20\%$ of daily read volume | RAM requirement for in-memory caching tier |

---

## 4. Architectural Paradigms & Structural Topology

```mermaid
flowchart TD
    subgraph ClientLayer["Edge & Client Tier"]
        Client["Web / Mobile / Public API Clients"] --> Ingress["Global Ingress / L7 Load Balancer"]
    end

    Ingress --> CoreMonolith

    subgraph CoreMonolith["Core System: Modular Monolith (In-Process)"]
        direction TB
        subgraph ModAuth["Auth & Identity Module"]
            A_Core["Logic"]
        end
        subgraph ModBilling["Billing & Subscription Module"]
            B_Core["Logic"]
        end
        subgraph ModCatalog["Product / Core Domain Module"]
            C_Core["Logic"]
        end
        ModAuth <== "In-Memory Facade\n(Zero Network Latency)" ==> ModBilling
        ModBilling <== "In-Memory Facade" ==> ModCatalog
    end

    subgraph DecomposedServices["Extracted Out-of-Process Services (Dedicated Compute Hosts)"]
        direction TB
        SvcTranscode["Heavy Processing Service\n(Media Transcoder / Ingestion Engine)"]
        SvcAI["Machine Learning Inference Service\n(GPU-Accelerated Cluster)"]
        SvcRealtime["Real-time Streaming Gateway\n(High-Concurrency WebSocket Node)"]
    end

    CoreMonolith -- "Private Internal gRPC / mTLS\n(Synchronous Fast-Path)" --> SvcTranscode
    CoreMonolith -- "Private Internal gRPC / mTLS" --> SvcAI
    CoreMonolith -- "Asynchronous Message Bus\n(Kafka / RabbitMQ)" --> SvcRealtime

    CoreDB[("Core RDBMS (PostgreSQL)\nIsolated Schemas: auth.*, billing.*, catalog.*")] --- CoreMonolith
    SvcTranscode --- ScratchStorage[("Worker Scratch Store / NVMe")]
```

---

## 5. Selective Service Decomposition Decision Framework

Do not decompose monolithic systems based on intuition or organizational trends. Evaluate candidate domains against the **5 Canonical Extraction Drivers** (Sam Newman & Martin Fowler standard):

```mermaid
flowchart TD
    Start["Candidate Domain Module"] --> D1{"1. Divergent Scaling Vector?\n(Traffic magnitude 10x-100x higher than core)"}
    D1 -- Yes --> Extract["Decompose to Out-of-Process Service"]
    D1 -- No --> D2{"2. Specialized Hardware Required?\n(GPU, High NVMe IOPS, Memory-only instances)"}
    D2 -- Yes --> Extract
    D2 -- No --> D3{"3. Blast-Radius & Fault Isolation?\n(Untrusted third-party, crash-prone computations)"}
    D3 -- Yes --> Extract
    D3 -- No --> D4{"4. Asymmetric Deployment Cadence?\n(Requires 20 deploys/day vs 1 deploy/week for core)"}
    D4 -- Yes --> Extract
    D4 -- No --> D5{"5. Strict Regulatory / Security Boundary?\n(PCI-DSS Cardholder Data, HIPAA PII isolation)"}
    D5 -- Yes --> Extract
    D5 -- No --> Retain["Retain Inside Modular Monolith (In-Process Module)"]
```

### Extraction Driver Analysis Matrix:

| Driver | Description | Architectural Consequence |
| :--- | :--- | :--- |
| **Divergent Scaling** | Domain throughput exceeds core system by orders of magnitude (e.g., telemetry streaming vs account billing). | Isolates horizontal auto-scaling nodes without scaling the entire monolithic memory footprint. |
| **Resource Heterogeneity** | Domain requires non-standard hardware profiles (e.g., CUDA GPU instances, extreme memory allocations). | Prevents costly over-provisioning of monolithic host infrastructure. |
| **Fault Isolation** | High probability of unhandled crash, memory leak, or infinite loops (e.g., user-supplied scripts, video transcoding). | Protects core business uptime by containing fatal process terminations to an isolated host. |
| **Deployment Cadence** | Autonomous team requires rapid iterations without coordinating full monolithic integration testing. | Enables decoupled CI/CD pipelines and independent release schedules. |
| **Regulatory Boundary** | Stringent compliance scopes auditing to a minimal infrastructure perimeter (e.g., PCI-DSS, SOC2). | Minimizes compliance audit scope and isolates sensitive network segments. |

---

## 6. Communication Protocols & Internal API Standards

Enforce strict protocol differentiation based on the execution boundary:

| Boundary Layer | Protocol | Wire Format | Transport Security | Network Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Client to Gateway** | HTTPS / HTTP/2 | JSON / REST | TLS 1.3 | Public Internet |
| **In-Process Modules** | Direct Function Call | Native Memory | In-Process Memory | Zero Network (Host RAM) |
| **Core to Extracted Service** | gRPC | Protocol Buffers (Protobuf) | Mutual TLS (mTLS) | Private VPC / Internal Subnet |
| **Asynchronous Events** | Kafka / RabbitMQ | Avro / Protobuf | SASL / TLS | Private Message Broker |
| **Real-time Push** | WebSocket / SSE | Binary / JSON | WSS (TLS) | Edge Ingress to Client |

---

## 7. Global Polyglot Storage Architecture

Data storage must be categorized by access pattern, consistency guarantee, and query complexity:

```mermaid
flowchart TD
    App["Application Layer\n(Core Monolith & Extracted Services)"]
    
    App --> Relational[("Transactional Core\n(PostgreSQL / MySQL)\n• ACID Transactions\n• Schema-isolated per module\n• Zero cross-module SQL joins")]
    App --> Cache[("Low-Latency Cache\n(Redis Cluster)\n• Sub-millisecond reads\n• Cache-Aside pattern\n• Distributed locking")]
    App --> Search[("Full-Text & Analytics\n(Elasticsearch / ClickHouse)\n• Read-model projections (CQRS)\n• Time-series telemetry\n• Aggregation dashboards")]
    App --> ObjectStore[("Immutable Blob Storage\n(S3-Compatible)\n• User assets, media, backups\n• Presigned upload URLs")]
```

### Rules of Persistence Isolation:
1. **Logical Schema Segregation in Core RDBMS:** 
   - When running inside the core modular monolith, distinct modules share the physical database engine but maintain dedicated schemas (`auth.users`, `billing.subscriptions`, `catalog.products`).
   - Direct cross-schema SQL `JOIN` statements across module boundaries are strictly forbidden. Cross-module data queries must pass through the owning module's Public In-Process Facade.
2. **Dedicated Datastores for Extracted Services:**
   - Any out-of-process extracted service owns its private persistent datastore. Shared database access across network boundaries is prohibited.

---

## 8. The 20-Point System Architecture Audit Checklist

Before finalizing any macro-level system architecture, verify compliance against these 20 verifiable criteria:

### A. Capacity & Quantified Requirements (Alex Xu)
- [ ] 1. Functional requirements define clear inputs, processing triggers, and outputs.
- [ ] 2. Non-Functional Requirements specify explicit SLAs: Latency (p95/p99), Availability (99.9% vs 99.99%), RPO, and RTO.
- [ ] 3. Average and Peak QPS are computed from explicit DAU and read/write ratios.
- [ ] 4. Multi-year storage growth accounts for payload size, indexing overhead, and metadata buffers.
- [ ] 5. Cache memory sizing is calculated using Pareto's 80/20 working-set rule.

### B. In-Process Modularity (Martin Fowler)
- [ ] 6. Core business domains reside within a strictly decoupled Modular Monolith.
- [ ] 7. In-process modules communicate exclusively via explicit Public Interfaces/Facades or in-memory events.
- [ ] 8. Zero direct cross-module private class imports or internal repository calls.
- [ ] 9. The database enforces logical schema separation per domain module.
- [ ] 10. Cross-module SQL `JOIN` queries across domain schemas are strictly prohibited.

### C. Out-of-Process Service Decomposition (Sam Newman)
- [ ] 11. Every extracted service is justified by at least one of the 5 Canonical Extraction Drivers.
- [ ] 12. Decomposed services are deployed independently without requiring synchronized core deployments.
- [ ] 13. Core-to-service communication traverses private subnets using strongly-typed gRPC/Protobuf.
- [ ] 14. Network calls between core and extracted services enforce strict deadlines and connection timeouts.
- [ ] 15. The core system implements graceful degradation if an extracted service becomes unreachable.

### D. Data & Storage Strategy (Chris Richardson)
- [ ] 16. Persistent datastores are matched to access patterns (RDBMS, In-Memory Cache, Columnar, Object Storage).
- [ ] 17. Extracted services do not share physical database connections with the core monolith.
- [ ] 18. Complex analytical reporting is offloaded from transactional tables to specialized read replicas or search indexes.

### E. Multi-Tier Ingress & Security (Alex Xu)
- [ ] 19. Public internet traffic terminates at an Edge Ingress/Load Balancer with Token Bucket rate limiting.
- [ ] 20. Out-of-process services reside within private subnets inaccessible from the public internet.

---

## 9. Implementation Handoff to Tier 2 & Tier 3

When the macro architecture design is established:
1. **If out-of-process distributed services are defined:**
   - Delegate distributed transaction, Saga orchestration, and Envoy mesh design to **`system-microservices-design`**.
2. **When implementing code for individual workers, daemons, or modules:**
   - Delegate state reconciliation, sticky leasing, atomic file swaps, and graceful draining to **`system-lifecycle-design`**.
