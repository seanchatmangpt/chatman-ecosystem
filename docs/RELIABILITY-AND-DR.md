# Reliability and Disaster Recovery — v26.8.18

## Reliability claim

v26.8.18 demonstrates real local reliability mechanisms and a real second-cluster cold-standby path. It does **not** claim high availability, multi-region fault tolerance, live replication, or a customer SLA.

The authoritative platform-specific details remain in:

- `platform-console/docs/SCOPE-AND-LIMITATIONS.md`
- `platform-console/docs/DISASTER-RECOVERY.md`
- `platform-console/docs/DR-SECOND-CLUSTER.md`
- `platform-console/docs/DATA-RESIDENCY.md`

This document states the cross-cutting ecosystem boundary.

## Failure domains

The primary environment is a local single-node kind cluster on one physical development machine/VM stack. Therefore:

```text
node failure
≈ control-plane failure
≈ etcd failure domain
≈ workload cluster failure domain
```

Mechanisms can be genuinely exercised inside that environment without the environment becoming HA.

## Observed recovery history

The repository documents a real etcd/bbolt corruption incident that required cluster reconstruction. That incident is evidence for the necessity of externalized manifests/evidence/recovery procedures; it is not evidence of transparent failover.

## Cold standby

A second distinct kind cluster was created as a cold-standby target and a manifest export/apply flow was exercised while preserving the primary cluster. Correct label:

`COLD_STANDBY`

Incorrect labels:

- HA;
- active-active;
- multi-region;
- live-replicated;
- automatic failover.

The second cluster proves a bounded reconstruction path to another cluster subject. It does not prove RPO/RTO or stateful replication.

## Data services

### Project Postgres

Current service shape: one Postgres StatefulSet/pod and PVC per project, with backup/restore mechanisms. There is no established streaming replica or continuous WAL-based point-in-time recovery equivalent to managed-cloud PITR.

A previously observed restore defect involving FK ordering is evidence that restore behavior requires executable validation, not documentation confidence.

### Redis and NATS

The current local managed-addon shapes provide real isolated service behavior. Their local persistence/availability model must not be expanded into a managed-cloud durability/SLA claim.

### Evidence/receipt state

Standing-relevant evidence that lives only on `emptyDir` is ephemeral. This applies to current ggen state and OCEL accumulation where documented. A system cannot claim replay/durability after restart until the state required for that replay is persisted and recovered successfully.

## Observability durability

Jaeger/Loki/OCEL data stores in the local profile are evidence tools for this deployment. Unless a component has an explicitly tested persistent-recovery path, observability history should be treated as local/ephemeral rather than a durable compliance archive.

## SLA boundary

The platform can calculate observed uptime and surface status. It does not make a contractual service-level commitment. Therefore:

```text
measured uptime != SLO contract != SLA != credits/remedy
```

Do not infer a customer-facing SLA from a status percentage.

## Recovery hierarchy

For each state class, recovery should be classified separately:

| State | Desired recovery proof |
|---|---|
| source/config | exact Git/content identity + checkout/materialization |
| canonical ontology/catalog | digest + schema/admission + regenerated projections |
| secrets/keys | protected backup/rotation + restore + verification |
| database | backup + restore + application-level integrity test |
| receipt ledger | durable copy + signature/hash-chain verify + replay |
| OCEL/process state | durable event/object store + digest + replay/discovery |
| cluster resources | manifest/graph export + apply + readiness/postcondition |
| external integrations | reauthorization + identity verification + live smoke test |

## DR execution contract

A DR exercise should record:

1. source exact SHA/config digest;
2. failure/trigger type;
3. recovery target identity;
4. transported state and intentionally excluded state;
5. commands/actions executed;
6. postconditions observed;
7. data/evidence loss measured;
8. receipt or experiment record;
9. rollback or next-state standing.

## Promotion requirements for HA claims

Before using `HA`, the system needs real evidence of at least:

- multiple failure domains;
- redundant control-plane/data components appropriate to the service;
- health detection and failover behavior;
- state replication semantics;
- failure injection against the exact topology;
- observed service continuity/postconditions;
- replayable evidence.

A second cold cluster alone does not satisfy these requirements.

## Falsifiers

Reliability standing falls if a claimed durable state disappears on restart, a restore completes but application invariants fail, the standby depends on unavailable unstated local state, a single-node mechanism is described as multi-region, or an uptime measurement is presented as a contractual SLA.
