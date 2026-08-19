# ggen as IaaS — v26.8.18 Observed State

Part of [00-OVERVIEW](00-OVERVIEW.md). This document began as a design proposal. It now records the **implemented manufacturing-substrate boundary** and the remaining evidence gaps.

## Standing

`PARTIAL_ALIVE`

The real ggen binary, sync pipeline, receipt generation/verification, tenant-scoped run directories, and deployed v26.8.18 service path exist. Durable per-tenant capsule/key/receipt custody is not closed.

## What IaaS means for ggen

The infrastructure primitive is not generic CPU alone. A lawful manufacturing capsule needs:

1. pinned manufacturing runtime/binary;
2. admitted ontology/config inputs;
3. isolated run workspace;
4. signing/verifying identity;
5. receipt/log custody;
6. bounded filesystem/network capability;
7. a refusal path when required evidence/authority cannot be provided.

Without receipt/key custody, raw compute can mutate a filesystem but cannot satisfy the ecosystem's standing contract.

## Implemented v26.8.18 path

`platform-console/services/ggen/app.py` implements a real `POST /provision` path that invokes a real ggen binary rather than a simulator. It executes the sync sequence, reads generated artifacts/receipts, and runs receipt verification.

The service resolves a tenant/project namespace and places each run under a namespace-specific workspace. The Deployment manifest targets the v26.8.18 live image, and later session evidence confirmed the rebuilt ggen-status pod was running/responding after deployment.

This closes the earlier “bare status stub” description. It does **not** prove one pod/capsule per tenant.

## Receipt and key custody

The service resolves signing material and supplies it to the ggen subprocess. The caller does not choose arbitrary key material per request.

Current ceiling:

- receipt/run state and service-local key material rely on local pod state unless separately operator-injected/persisted;
- `emptyDir`-backed state does not survive pod recreation;
- historical receipt verification therefore depends on preserving the corresponding verifying identity outside ephemeral lifecycle.

A production IaaS rail needs durable, tenant-isolated receipt/key custody and restart/recovery proof.

## Admission

Current service refusal includes real dependency and tenant-resolution failures. The remaining IaaS-level admission gap is stronger capsule admission: refuse a standing-sensitive run when required durable receipt/key custody or isolation contract is absent, rather than allowing execution and documenting ephemerality afterward.

## Tenant ontology

Caller-supplied ontology content is materialized inside the tenant-scoped run. At this layer it is input observation/candidate semantics, not ambient authority. Validation/curation/trust policy belongs to higher semantic/admission layers.

## Required next evidence

Promote a future `ggen_iaas` rail only after observing:

1. isolated capsule identity per admitted tenant/run;
2. persistent receipt/log storage;
3. persistent or externally managed signing/verifying identity;
4. restart/replacement recovery;
5. receipt verification after recovery;
6. cross-tenant negative isolation tests;
7. exact-subject receipt/replay evidence.

## Non-claims

v26.8.18 IaaS does not claim:

- per-tenant VM/pod isolation;
- KMS/HSM custody;
- multi-region durability;
- HA;
- SaaS purchase/entitlement;
- that a generated receipt is automatically an actuation receipt for an external deployment.

## See also

- [02 — ggen as PaaS](02-GGEN-AS-PAAS.md)
- [03 — ggen as SaaS](03-GGEN-AS-SAAS.md)
- [04 — BRCE cross-cutting](04-GGEN-BRCE-CROSS-CUTTING.md)
- [`../../GGEN-SERVICE.md`](../../GGEN-SERVICE.md)
