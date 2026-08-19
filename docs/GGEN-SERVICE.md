# ggen Service Contract — v26.8.18

## Standing

The repository-level ggen rail is `PARTIAL_ALIVE` in `catalog/rails.toml`. This document describes the implementation that standing currently covers and the gaps it does not.

## Service layers

The v26.8.18 implementation separates three useful commercial/deployment views without pretending they are three independent products:

| Layer | Current state | Claim ceiling |
|---|---|---|
| IaaS/manufacturing capsule | real binary execution and signed receipt path | process-level isolation/durability still bounded |
| PaaS/managed provisioning | real HTTP `/provision`, tenant namespace/workspace resolution, attempt logging | one shared service process; standing storage/key lifecycle incomplete |
| SaaS/capability commerce | marketplace/search metadata exists | purchase, entitlement, billing, metering and fulfillment contract incomplete |

All three remain governed by the same constitutional rules: `A = μ(O*)`, `SELECT != CONSTRUCT != DO`, and zero unreceipted actuation.

## `POST /provision`

The endpoint executes a real ggen pipeline rather than returning a simulated success. Its responsibilities include:

1. validate/parse the request envelope;
2. resolve the tenant/project to a Kubernetes namespace/workspace boundary;
3. materialize ontology/config inputs under a run-specific directory;
4. invoke the configured real `ggen` binary;
5. install declared packs;
6. execute `ggen sync run`;
7. read the resulting receipt/artifacts;
8. invoke receipt verification;
9. return the actual result or an explicit failure;
10. append an attempt record.

A missing real ggen binary is a service-unavailable condition, not a reason to synthesize output.

## Tenant scoping

Runs are scoped under a namespace-specific workspace rather than one flat run directory. This is a real reduction in cross-tenant collision risk. It is **not** equivalent to a per-tenant pod/capsule with independently enforced compute, filesystem, key and network boundaries.

A future `ggen_iaas` rail should distinguish process-level workspace isolation from a fully isolated capsule.

## Signing-key lifecycle

The service resolves signing material by operator configuration or local persisted/generated seed according to its implemented precedence. The caller does not supply arbitrary signing material per request.

Current boundary: standing key custody is not yet a durable, per-tenant KMS/HSM-style contract. A restart or local state loss must not be described as preserving historical signing continuity unless the backing storage/key mechanism has been independently verified.

## Receipts

The service returns actual ggen receipt material and a receipt-verification result. The HTTP response also identifies the PaaS origin/attempt context.

Do not collapse:

```text
HTTP origin metadata != signed receipt origin
receipt generated != receipt durably retained
receipt verified once != replay closed
```

At the reviewed implementation point the signed receipt's own origin semantics and the HTTP envelope are not identical. Documentation must state that rather than implying the HTTP label was cryptographically bound into bytes it was not.

## Durability

Run state, receipts, attempt logs, and signing material that live on ephemeral pod storage do not survive pod destruction by definition. `emptyDir` is therefore a standing ceiling.

Durability closure requires:

- explicit persistent volume/object/ledger design;
- recovery after pod replacement;
- historical verifying-key availability;
- receipt-chain/replay verification after recovery;
- tenant isolation evidence.

## Marketplace bridge

The ggen-marketplace service is no longer a health-only stub. At the observed v26.8.18 point its `/packs` registry bridge returned 151 pack records, with a query surface over registry metadata.

This proves marketplace metadata exposure, not full semantic closure. The bridge does not make every pack's domain ontology triples queryable through one complete canonical graph, and a pack being listed does not establish its own `ALIVE` standing.

## SaaS boundary

The following are still absent as one closed product path:

- authenticated subscription/entitlement identity;
- purchase/order state;
- trust-tier-aware buyer authorization;
- receipt-tied usage metering;
- price/billing/settlement integration;
- durable tenant artifact delivery;
- signed expiring delivery URLs bound to a purchased capability;
- purchase -> fulfillment -> actuation receipt -> independent verification replay.

Therefore `/provision` must not be renamed “SaaS complete.”

## Trust and admission

Pack IDs, ontology content and generated artifacts are input/candidates, not authority. Any future unattended fulfillment must preserve hard refusal at trust/authority boundaries. Soft warnings are insufficient for writes that cross tenant or production consequence boundaries.

## Recommended rail split

The current single `ggen` rail is useful but conflates layers with different evidence ceilings. A later canonical change may split it into:

```text
ggen_iaas   -- isolated manufacturing + durable receipt/key custody
ggen_paas   -- tenant-scoped managed pipeline + brokered actuation
ggen_saas   -- entitlement/purchase/metering/fulfillment receipt path
```

That split should occur only with real evidence paths for each rail; it is not documentation-only promotion.

## Falsifiers

Lower standing if:

- `/provision` returns success without invoking a real ggen binary;
- one tenant can read/write another tenant's workspace or keys;
- a receipt is claimed durable after ephemeral state loss;
- marketplace listing is used as pack execution standing;
- a purchase/entitlement claim is made without a real commerce state machine;
- a PaaS write bypasses the required authority/receipt path.
