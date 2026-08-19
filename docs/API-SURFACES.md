# API and Capability Surfaces — v26.8.18

This document maps **capability to transport to authority**. Transport availability never implies permission to actuate.

## Constitutional path

```text
parse -> route -> admit/refuse -> construct -> verify -> authority admission -> BRCE -> receipt -> replay -> standing
```

`SELECT`, `CONSTRUCT`, and `DO` are different authority classes. CLI, HTTP, MCP, A2A, scheduled governors, and hooks are projections over capabilities; none acquires ambient `DO` authority merely because it can invoke code.

## Composition-root surfaces

| Surface | Implementation | Authority ceiling | Evidence role |
|---|---|---|---|
| Rust library | `crates/ecosystem-core` | construct/verify constitutional objects | identity, authority, receipt, Crown algebra |
| Runtime | `crates/ecosystem-runtime` | bounded adapters; brokered effects only | storage/governor/connector behavior |
| CLI | `apps/ecosystem-cli` | process interface; subcommand-specific | executable operator/CI boundary |
| MCP | runtime MCP boundary | read-only Crown inspection in admitted subset; mutations refused/brokered | protocol projection, not independent authority |
| GitHub connector | runtime + CI | read/observe at v26.8.18 control-plane boundary unless separately authorized | exact repo/head observation |
| Document connector | runtime | deterministic identity/revision normalization | document evidence, not remote mutation grant |

## Platform-console HTTP/UI surface

`platform-console` is a deployable application surface separate from the Rust constitutional core. Its API routes are governed by session/RBAC checks and Kubernetes/service-specific policy.

Major capability groups include:

- project and database provisioning;
- cache and queue lifecycle;
- backups/restore;
- resource usage, cost, budget and quota enforcement;
- IAM/session/admin surfaces;
- GitOps visibility;
- policy/admission and vulnerability-scan views;
- audit, logs, metrics, traces, topology and custom dashboards;
- signed storage access and edge caching;
- ggen/ggen-marketplace integration;
- OCEL process-evidence status.

The UI is not an authority source. Server-side routes must perform the same admission and role checks regardless of how a request was initiated.

## ggen service

### `POST /provision`

The v26.8.18 ggen service runs a real `ggen` binary through the provision sequence, scopes work by tenant/project namespace, returns generated artifacts and receipt verification data, and records attempts. It is `PARTIAL_ALIVE`, not a complete SaaS contract. See `GGEN-SERVICE.md`.

### Marketplace registry

The marketplace bridge exposes pack metadata through HTTP and, at the observed implementation point, resolved 151 pack records. This is registry/search capability, not purchase/entitlement/billing.

## Observability and process evidence

| Surface | Source | Authority |
|---|---|---|
| Prometheus metrics | live cluster signals | observe only |
| Jaeger traces | OTel Collector fan-out | observe only |
| Loki logs | Promtail aggregation | observe only |
| standing weaver | OTel Collector fan-out | verification/evidence only |
| OCEL accumulator | OTel Collector fan-out | process-evidence construction only |
| `/ocel-log` | accumulator status/discovery proxy | viewer-gated read |

Telemetry may construct evidence or candidate intents. It does not authorize mutations.

## Castle / planner surfaces

Castle is exposed as bounded one-shot execution for an allowlisted verb set. Planner output remains `CONSTRUCT`; an execution plan does not gain `DO` authority from being selected. The heavier GymAct/Castle execute path remains a closure item until the exact BRCE authority/receipt path is observed end to end.

## Interface equivalence rule

Two interfaces are equivalent only when they route to the same admitted capability semantics and preserve the same authority/refusal/receipt contract. Similar names or payloads are not sufficient.

For a capability `c` projected to transports `t_i`:

```text
semantic(c) must be invariant
admission(c, t_i) must not weaken
DO(c, t_i) must still factor through BRCE
receipt(c, t_i) must bind the realized consequence
```

## Failure semantics

Public surfaces should fail closed:

- unauthenticated -> 401/refusal;
- insufficient role -> 403/refusal;
- missing real dependency -> explicit unavailable/error, not synthetic success;
- invalid/malformed request -> typed rejection;
- ambiguous timeout -> `Ambiguous`, not assumed success;
- missing authority -> `AwaitingAuthority`/refusal rather than execution.

## Not yet claimed

v26.8.18 does **not** claim:

- complete MCP or A2A protocol coverage across every capability;
- ambient remote mutation authority;
- complete ggen SaaS commerce;
- general-purpose wasm4pm discovery through `/ocel-log` while `/discovery` remains incomplete;
- multi-region control-plane semantics from a single-node local deployment.
