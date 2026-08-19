# Architecture — v26.8.18

> Reviewed implementation baseline: `seanchatmangpt/chatman-ecosystem@2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`

## Constitutional dependency direction

```text
ecosystem-core
      ↑
ecosystem-runtime
      ↑
ecosystem-cli
```

`ecosystem-core` owns constitutional types and remains intentionally independent of application/runtime frameworks. Runtime and CLI layers may depend inward; the constitutional layer must not acquire ambient framework authority.

## System layers

v26.8.18 has four distinct layers. They must not be collapsed into one maturity claim.

### 1. Constitutional control plane

Owns:

- stable typed identities and exact subjects;
- admission and standing transitions;
- authority classes;
- canonical catalog loading and validation;
- BLAKE3 receipt sealing/verification;
- deterministic projections;
- Crown evaluation and refusal semantics.

### 2. Runtime and interface adapters

Owns replaceable implementations for:

- memory and SQLx/SQLite state;
- bounded governor execution, idempotency, and timeout ambiguity;
- MCP JSON-RPC handling;
- GitHub/document normalization;
- CLI/operator interaction.

Adapters construct observations and intentions. They do not manufacture constitutional authority.

### 3. Deployable platform surface

`platform-console/` is the current local deployable control surface. At the reviewed subject it includes evidence-backed mechanisms for:

- Kubernetes project provisioning and resource quotas;
- per-project Postgres, Redis, and NATS/JetStream service shapes;
- local-admin/GoTrue/OIDC session paths and role enforcement;
- Istio STRICT mTLS and NetworkPolicy segmentation;
- CEL ValidatingAdmissionPolicy rules and vulnerability-scan admission controls;
- GitOps read-only visibility;
- signed storage access, edge caching, backup/restore, dashboards, cost visibility, and quota enforcement;
- topology views using shared service-discovery data;
- Prometheus metrics, Jaeger tracing, Loki/Promtail log aggregation, and OTel Collector fan-out;
- an OCEL v2 accumulator and `/ocel-log` dashboard driven by the same real telemetry stream;
- ggen and ggen-marketplace service bridges;
- bounded Castle execution and AutoFDE-lab planner integration;
- cold-standby disaster-recovery materialization.

This layer is **not** the constitutional core. A live Kubernetes behavior does not rewrite standing law, and a constitutional theorem does not prove a live Kubernetes behavior.

### 4. Ecosystem composition graph

The repo binds independently owned component repositories into release subjects. A component edge must preserve:

```text
repository + ref + exact SHA + role + dependencies + standing + evidence
```

`release/v26.9.1/manifest.toml` is a future composition subject. It is deliberately separate from the v26.8.18 operational snapshot.

## Authority geometry

Authority is exact, not ordinal.

```text
SELECT != CONSTRUCT != DO
```

Examples:

- a planner may select a candidate without authorization to execute it;
- ggen may manufacture an artifact without conferring deployment standing;
- an MCP handler may expose a capability without receiving permission to mutate;
- repository administration does not imply release, merge, communication, spend, or production authority.

All consequential actuation must factor through the brokered authority boundary:

```text
candidate intent
  -> admission
     -> REFUSED
     -> admitted action
        -> BRCE
        -> consequence + receipt
```

## Receipt boundary

Receipts distinguish at least:

- subject identity;
- observation/admission context;
- executed command/action;
- authority used;
- changed artifacts/state;
- verification and observed consequence;
- exclusions/failures;
- predecessor/replay identity.

A digest recomputed during verification is not evidence that a receipt was sealed at actuation time. Verification must bind the originally emitted receipt and exact subject.

## ggen boundary

The v26.8.18 ggen service exposes real manufacture through `POST /provision`, invoking a configured ggen binary rather than simulating generation. The reviewed implementation also resolves per-tenant namespace/workspace identity and returns signed receipt material.

The canonical rail remains `PARTIAL_ALIVE`. The current boundary is therefore:

```text
ggen IaaS manufacture        -> implemented evidence
ggen PaaS managed provision  -> implemented evidence, bounded
marketplace registry         -> bridged metadata catalog
ggen SaaS commerce           -> incomplete
```

Purchase, entitlement, external billing/metering, and full product-lifecycle semantics are not inferred from `/provision` or `/packs`.

## Observability and process-evidence boundary

v26.8.18 extends the platform from metrics-only observation to a multi-signal local stack:

```text
workload / Envoy spans
      -> OTel Collector
          -> Jaeger
          -> standing weaver live-check
          -> OCEL v2 accumulator
               -> deduplicated append-only JSONL
               -> canonical OCEL v2 JSON
               -> /ocel-log status/dashboard
               -> /discovery (incomplete, fail-closed)

container logs
      -> Promtail
      -> Loki

metrics
      -> Prometheus
```

The OTel Collector is the single mesh tracing provider at the reviewed head and fans out to three downstream consumers. Direct Envoy-to-weaver and dual-Istio-provider approaches had already failed in live testing and were replaced by this fan-out topology.

The OCEL accumulator is a real third consumer: live traffic caused its event/object counts to grow from 24→29 events and 14→17 objects in the observed run. Its storage is currently `emptyDir`, and the wasm4pm-backed `/discovery` endpoint remains incomplete. The dashboard correctly surfaces that incomplete edge as failure rather than fabricating a result.

The remaining unattended-traffic boundary is also explicit: the local cluster still does not provide self-sustaining continuous traffic generation for the standing pipeline.

## Security boundary

The local platform has real tested controls, including restricted PodSecurity, mTLS, NetworkPolicy isolation, admission policies, vulnerability scanning, RBAC, envelope-encryption work, and tamper-evident audit evidence. These mechanisms establish only their tested local properties.

They do not imply:

- multi-region blast-radius isolation;
- independent key custody equivalent to a managed KMS/HSM;
- external certification;
- a complete adversary model for every ecosystem repository.

## Deployment topology ceiling

The primary live environment described by the evidence is a single-node kind cluster on one physical machine. A second kind cluster exists as cold standby. Therefore:

```text
real mechanism != hyperscaler topology
cold standby != HA
second cluster != multi-region
measured uptime != SLA
readiness evidence != certification
```

The detailed boundary is maintained in `platform-console/docs/SCOPE-AND-LIMITATIONS.md`.

## Standing boundary

A Git SHA is identity evidence only. `ALIVE` requires observed execution against the exact admitted subject under the owning verifier with receipt/replay evidence.

Use the release standing states distinctly:

`UNKNOWN | PARTIAL_ALIVE | ALIVE | BLOCKED | BUILD_BROKEN | UNSUPPORTED`

Typed `REFUSED` outcomes are behavior, not a substitute for one of those standing states.

## Version boundary

- `v26.8.18`: current operational/documentation snapshot.
- `v26.9.1`: next dependency-closed ecosystem composition crown.

Do not mass-rewrite the v26.9.1 theorem/manifests to v26.8.18. They describe a different admitted subject.
