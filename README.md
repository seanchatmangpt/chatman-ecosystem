# Chatman Ecosystem — v26.8.18

The constitutional control plane, executable platform surface, project graph, documentation registry, automation-policy layer, and evidence ledger for the Chatman Ecosystem.

> **Current operational snapshot:** `v26.8.18`
> **Reviewed implementation baseline:** `2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`
> **Ecosystem standing:** `PARTIAL_ALIVE`
> **Next composition crown:** `v26.9.1` (future release graph, not renamed or collapsed into this snapshot)

The governing equations remain:

```text
A = μ(O*)
R = receipt(A)
```

`O*` is admitted observation; `μ` is lawful manufacture; `A` is the resulting artifact or consequence; `R` binds identity, authority, execution, verification, consequence, and replay.

## Core invariant

> **Zero unreceipted actuation.**

Models, planners, generated code, hooks, proofs, connectors, MCP handlers, and workflow engines may construct candidates or intents. They do not receive ambient `DO` authority. Consequential mutation crosses the brokered authority boundary or is refused.

## v26.8.18 at a glance

The 2026-08-18 implementation pass moved the repository far beyond its original v0.1 control-plane-only surface. At the reviewed implementation baseline the repo contains:

- the Rust constitutional core, runtime adapters, CLI, receipts, catalog, deterministic projections, Crown gates, and Gall capsule;
- a live-tested Kubernetes platform console with project provisioning, RBAC, policy-as-code admission, Istio mTLS, NetworkPolicy isolation, vulnerability scanning, GitOps visibility, audit evidence, dashboards, quota enforcement, and topology views;
- per-project Postgres, Redis, and NATS/JetStream managed-service shapes with bounded operator APIs;
- Prometheus observability plus Jaeger tracing, Loki/Promtail centralized logs, and an OpenTelemetry Collector fan-out to Jaeger, a standing-weaver live-check, and an OCEL v2 accumulator;
- a live `/ocel-log` surface backed by admitted OTLP-derived events/objects, while the deeper `/discovery` bridge remains fail-closed and incomplete;
- ggen `POST /provision` integration using a real ggen binary, per-tenant workspace/namespace resolution, signed receipt output, and a marketplace registry bridge exposing 151 pack records at the observed implementation point;
- Castle as a bounded, allowlisted one-shot lifecycle surface and a second planner path through AutoFDE-lab;
- a cold-standby second kind cluster and disaster-recovery materialization path;
- SOC 2 **readiness evidence**, including a generated binder and refusal of compliance/certification claims without an independent audit.

The evidence ceiling remains explicit. `v26.8.18` does **not** mean Fortune-5 production deployment, SOC 2 certification, true multi-region HA, contractual SLA, complete ggen SaaS commerce, or full GymAct `DO` integration.

See [`docs/v26.8.18-release.md`](docs/v26.8.18-release.md) for the release receipt, exact boundaries, and falsifiers.

## Workspace

| Surface | Role |
|---|---|
| `crates/ecosystem-core` | identities, exact subjects, standing, authority, catalog, receipts, projections, Crown evaluation |
| `crates/ecosystem-runtime` | replaceable runtime/storage/governor/MCP/connector adapters |
| `apps/ecosystem-cli` | fail-closed operator and CI interface |
| `platform-console/` | deployable platform/PaaS control surface and live evidence corpus |
| `catalog/` | canonical TOML registry; generated documentation does not outrank it |
| `receipts/` | source receipts and replay evidence |
| `views/generated/` | deterministic projections; do not hand-edit |
| `soc2/` | generated SOC 2 readiness binder; not an auditor opinion |
| `release/v26.9.1/` | future dependency-closed composition target |
| `docs/` | constitutional thesis, operational handbook, release notes, and design records |

## Current architecture

```text
observation O
  -> admission / refusal
  -> O*
  -> SELECT / CONSTRUCT
  -> verification
  -> authority admission
  -> BRCE DO
  -> consequence A
  -> receipt R
  -> replay / observation
  -> standing
```

The composition root does not make every repository one monolith. Repository boundaries remain ownership and evidence boundaries. A Git SHA proves identity, not execution standing.

## Standing law

Use the release-standing states distinctly:

`UNKNOWN | PARTIAL_ALIVE | ALIVE | BLOCKED | BUILD_BROKEN | UNSUPPORTED`

Typed refusal is behavior, not a degraded success state. Inspection is not execution; workflow existence is not a successful run; a named receipt is not proof that its digest/replay verified.

At the reviewed implementation baseline, `catalog/rails.toml` marks the repo-level ggen rail `PARTIAL_ALIVE`. That alone prevents an ecosystem-wide `ALIVE` claim for this snapshot.

## Admission and replay

For the Rust composition root:

```bash
./scripts/crown.sh

cargo run --locked -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --locked -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --locked -p ecosystem-cli --bin ecosystem -- projection check
cargo run --locked -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --locked -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --locked -p ecosystem-cli --bin ecosystem -- crown --verify
```

For the future `v26.9.1` release graph:

```bash
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/verify_release.py --check-refs --require-alive
```

The strict release command is intentionally allowed to fail until every required exact component subject has independently earned `ALIVE`.

## v26.8.18 claim ceiling

The current implementation has real live-cluster evidence, but the following remain outside the admitted claim:

- no multi-node or multi-region HA; the primary platform is still a single-node kind cluster on one physical machine;
- the second cluster is cold-standby DR, not active/active or live replicated failover;
- no contractual customer SLA;
- project Postgres uses a single instance and snapshot-style backup/restore rather than streaming replication and continuous PITR;
- SOC 2 material is readiness evidence only; certification/attestation requires an independent licensed auditor;
- ggen IaaS/PaaS paths have implementation evidence, while SaaS purchase, entitlement, metering, and billing remain incomplete;
- GymAct verification exists, but the heavier GymAct/Castle `execute` path is not yet the admitted BRCE `DO` route;
- the OpenTelemetry/standing-weaver/OCEL pipeline is wired and live-tested, but unattended continuous traffic generation remains blocked on the reviewed local cluster configuration;
- OCEL accumulation/status is live, while `/discovery` remains a fail-closed incomplete edge rather than a fabricated process-mining result.

See [`platform-console/docs/SCOPE-AND-LIMITATIONS.md`](platform-console/docs/SCOPE-AND-LIMITATIONS.md) for module-level boundaries.

## Gall capsule

The Gall capsule remains a bounded, dependency-light executable proof of four checkpoints:

```text
GALL-S0 source admission
  -> GALL-S1 receipt-bearing BRCE
  -> GALL-S2 gateway/session/channel routing
  -> GALL-S3 capability-fenced WebAssembly skill
  -> GALL_CROWN
```

Its `ALIVE` standing applies only to its exact executed capsule subject and fixtures. It does not confer aggregate standing on MCPP, wasm4pm, ggen, mfact, or any other source repository.

## Forward-deployment operating loop

```text
parse
→ route
→ admit or refuse
→ diagnose / repair
→ construct
→ actuate
→ observe consequence
→ verify
→ receipt
→ replay / hook
→ standing
```

The ecosystem objective is to reduce manufactured coordination and rediscovery while preserving exact authority, evidence, and reversibility.

## v26.9.1 relationship

`v26.9.1` remains the next composition-crown target. Its manifest and long-form constitutional thesis deliberately stay versioned `26.9.1`; they describe the dependency-closed future release theorem rather than the current 2026-08-18 deployed snapshot.

The crown question remains:

> **Where is the receipt?**

Useful entry points:

- [`docs/v26.8.18-release.md`](docs/v26.8.18-release.md) — current release snapshot and review receipt
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — current architecture and authority boundaries
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — verification, operation, and evidence rules
- [`docs/00-introduction.md`](docs/00-introduction.md) — constitutional book entry point
- [`docs/jira/v26.8.18/00-OVERVIEW.md`](docs/jira/v26.8.18/00-OVERVIEW.md) — reconciled ggen IaaS/PaaS/SaaS work package
- [`status/README.md`](status/README.md) — generated fleet projection; may lag current heads until regenerated
- [`release/v26.9.1/manifest.toml`](release/v26.9.1/manifest.toml) — next-release component graph
