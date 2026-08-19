# ggen IaaS/PaaS/SaaS — v26.8.18 Reconciled Status

This directory began as a four-part design proposal. By the reviewed repository subject
`1ed4972318467c5bfb5d283505893a361536d37a`, implementation work has overtaken parts of the
proposal. This index therefore records the **current evidence state** instead of continuing to
claim that no code changes accompany the ticket set.

The governing boundary remains `CONSTITUTION.md`'s zero-unreceipted-actuation rule. Successful
manufacture, API exposure, marketplace discovery, and product commerce are different closures
and must not be collapsed into one "ggen is SaaS" claim.

## Current layer state

| Layer | v26.8.18 state | Evidence ceiling |
|---|---|---|
| IaaS / manufacturing capacity | implemented evidence | real configured ggen binary is invoked by `platform-console/services/ggen/app.py`; no simulated success path |
| PaaS / managed provision | `PARTIAL_ALIVE` | `POST /provision`, tenant namespace/workspace resolution, attempt logging, and signed receipt return exist; repo-level `ggen` rail remains `PARTIAL_ALIVE` |
| Marketplace/catalog | implemented metadata bridge | platform registry bridges 149 content packs plus the original resolver records, yielding 151 observed pack records; generic bridge does not expose every pack's full domain ontology |
| SaaS / commercial capability | incomplete | no complete purchase, entitlement, billing/metering, or fulfillment lifecycle |
| Cross-cutting BRCE | partial | provisioning is bounded and receipted, but the full product lifecycle is not yet a single admitted commerce→manufacture→fulfillment receipt chain |

## What changed since the proposal was written

### IaaS

`platform-console/services/ggen/app.py` now exposes a real `POST /provision` route that runs an
actual configured `ggen` binary through its initialization/install/sync/receipt path. Failure to
configure the real binary fails closed rather than manufacturing a synthetic success.

### PaaS

Provisioning now resolves a tenant/project namespace and places work under a bounded tenant
workspace. Attempts are recorded and responses carry provisioning origin metadata. The
`ggen-status` service was rebuilt and redeployed during the v26.8.18 work sequence, closing the
original "status stub only" description in this index.

This does **not** establish a dedicated compute capsule per tenant, durable receipt custody
across every pod restart, or globally `ALIVE` standing.

### Marketplace

The platform's marketplace service moved from a health-only stub to `GET /packs` and
`POST /query`, then bridged the content marketplace into the resolver format. The observed
registry reached 151 pack records. This is real catalog/service behavior, but it remains a
metadata projection: full per-pack domain triples are not automatically queryable through the
generic bridge.

### SaaS

The original SaaS ticket remains materially open. A tenant-facing catalog plus provisioning
is not equivalent to a product commerce system. The following still need executable semantics
and receipts:

- capability purchase/order;
- entitlement and revocation;
- metering tied to the admitted capability;
- billing/settlement integration;
- fulfillment identity binding buyer, entitlement, manufacture, consequence, and receipt;
- replay/refund/remediation semantics where applicable.

## Tickets

1. [01-GGEN-AS-IAAS](01-GGEN-AS-IAAS.md) — now partly realized; read as the design contract and
   remaining IaaS closure criteria, not as a statement that no implementation exists.
2. [02-GGEN-AS-PAAS](02-GGEN-AS-PAAS.md) — now partly realized and represented by the canonical
   repo-level `ggen` rail in `catalog/rails.toml`; current standing is `PARTIAL_ALIVE`.
3. [03-GGEN-AS-SAAS](03-GGEN-AS-SAAS.md) — remains the principal open product layer. Discovery
   and provision are prerequisites, not proof of commerce/entitlement closure.
4. [04-GGEN-BRCE-CROSS-CUTTING](04-GGEN-BRCE-CROSS-CUTTING.md) — remains the authority contract
   that prevents the three layers from becoming three ambient mutation paths.

## Definition of done for v26.8.18 documentation

- Statements distinguish observed implementation from proposed next work.
- No layer inherits `ALIVE` from a neighboring layer.
- `/provision` is not described as SaaS purchase/entitlement.
- Marketplace record count is described as the observed bridge state, not full ontology/class
  closure.
- Zero-unreceipted-actuation remains invariant across every future fulfillment path.
- Generated status documents are not hand-edited to make the release appear healthier.

## Next standing-changing receipts

### IaaS/PaaS

- durable receipt/attempt custody under an explicitly verified storage policy;
- signed origin/tenant binding in the receipt payload itself where required by the owning
  receipt schema;
- stronger tenant execution isolation if the desired claim is capsule-per-tenant rather than
  process/workspace isolation;
- exact-head replay of provision success and refusal fixtures.

### SaaS

A minimum complete proof must show:

```text
select capability
→ establish entitlement
→ authorize purchase/fulfillment
→ manufacture exact subject
→ verify consequence
→ meter/bind commercial event
→ emit receipt
→ replay/reconcile
```

with typed refusal for missing/expired entitlement, tampered request, duplicate fulfillment,
insufficient authority, failed manufacture, and receipt mismatch.

## See also

- [`../../../CONSTITUTION.md`](../../../CONSTITUTION.md)
- [`../../v26.8.18-release.md`](../../v26.8.18-release.md)
- [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
- [`../../OPERATIONS.md`](../../OPERATIONS.md)
- [`../../../catalog/rails.toml`](../../../catalog/rails.toml)
- [`../../../platform-console/docs/SCOPE-AND-LIMITATIONS.md`](../../../platform-console/docs/SCOPE-AND-LIMITATIONS.md)
