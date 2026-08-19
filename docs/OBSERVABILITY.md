# Observability — v26.8.18

## Purpose

Observability in v26.8.18 is an evidence substrate, not a standing oracle. Metrics, traces, logs, and process events can show what was observed; they do not by themselves prove admission, authorization, receipt integrity, replay, or class closure.

## Current topology

```text
workload / Envoy spans
        |
        v
OTel Collector (istio-system)
   |        |             |
   |        |             +--> OCEL v2 accumulator --> /ocel-log
   |        +----------------> standing weaver live-check
   +-------------------------> Jaeger

container logs --> Promtail --> Loki --> /log-search
metrics ---------------------> Prometheus --> status/dashboards
```

The OTel Collector is deliberately the single tracing provider for the mesh and performs fan-out downstream.

## Why the Collector exists

Two earlier paths were falsified by live execution:

1. direct Envoy-to-weaver OTLP/gRPC transport did not produce a working standing path;
2. the installed Istio Telemetry API rejected the attempted dual-tracing-provider configuration.

The lawful repair was not to claim those paths worked. The implementation introduced one OTel Collector provider and moved fan-out behind it.

## Jaeger

Jaeger provides trace storage/query for the observed local deployment. A real protocol defect was found during implementation: without an explicit gRPC protocol hint, the upstream path negotiated incorrectly. `appProtocol: grpc` on the Service path repaired the observed OTLP/gRPC behavior.

Scope ceiling:

- real traces were observed;
- the local Jaeger profile uses bounded/local storage characteristics;
- no durable multi-region APM/SLA claim follows.

## Loki / Promtail

Promtail tails container logs and ships them to Loki. `/log-search` queries the actual aggregation backend rather than a fabricated in-memory list.

Observed implementation defects included storage/schema configuration and relabel/synchronization issues; those were repaired rather than hidden. The current claim is centralized local-cluster log aggregation, not global retention/compliance storage.

## standing weaver

The standing-weaver path consumes OTLP emitted by the Collector. Three material live defects were discovered while making this path real:

- a stale Service/Endpoints object shadowed the intended Deployment-backed endpoint;
- the Collector's default gzip compression was rejected by weaver's tonic OTLP receiver, requiring `compression: none` for that exporter;
- NetworkPolicy initially blocked Collector-to-weaver traffic.

The standing process also required a non-default inactivity policy so the Deployment did not exit after an idle interval.

After repair, real gateway requests increased the Collector's accepted-span counter and reached the standing path. The remaining limitation is not connectivity: **continuous unattended traffic generation is not established in this local topology**.

## OCEL fan-out

The Collector's third downstream is the OCEL accumulator. It transforms admitted OTLP span evidence into object-centric event-log material. Live traffic was observed increasing the accumulator from 24 to 29 events and 14 to 17 objects.

See `OCEL-PROCESS-EVIDENCE.md` for the process semantics and current `/discovery` boundary.

## Evidence hierarchy

Observability evidence should be interpreted in this order:

```text
signal exists
  < signal reaches intended backend
  < signal corresponds to exact subject/request
  < postcondition is independently observed
  < receipt binds consequence
  < replay reproduces admitted consequence
```

A dashboard screenshot or HTTP 200 is not the top of this ladder.

## Security boundary

Telemetry receivers must not become unauthenticated escape paths. A prior static Endpoint configuration exposed an unintended mesh-to-host OTLP route; it was removed, and ingress was constrained. Future observability changes must preserve:

- namespace/network isolation;
- least-privilege service identity;
- no ambient actuation from telemetry payloads;
- fail-closed behavior when a downstream verifier is unavailable.

## Persistence boundary

Several current observability components use local/ephemeral storage suitable for this v26.8.18 local evidence environment. Do not infer production retention, multi-zone durability, or disaster-recovery guarantees from successful local ingestion.

## Operational checks

A standing check should answer, separately:

1. Is the producer generating real signals?
2. Is the Collector accepting them?
3. Is each configured exporter accepting them?
4. Can the downstream query surface retrieve the corresponding exact signal?
5. Does the signal bind to the intended subject and time window?
6. If the claim is consequential, where is the actuation receipt and replay evidence?

## Falsifiers

The observability claim is invalidated if:

- spans are generated but not accepted by the Collector;
- one exporter silently drops while aggregate Collector health remains green;
- a query UI returns synthetic/fallback data after backend failure;
- an OTLP endpoint bypasses intended network/security boundaries;
- a process-evidence consumer claims discovery when its real discovery edge is unavailable;
- telemetry existence is used as a substitute for authority or consequence verification.
