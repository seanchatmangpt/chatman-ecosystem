# ggen as SaaS — v26.8.18 Gap Contract

Part of [00-OVERVIEW](00-OVERVIEW.md). This layer remains intentionally **incomplete**. v26.8.18 has real provisioning and marketplace metadata, but not a closed capability-commerce product.

## Standing

`UNSUPPORTED` for the complete purchase/entitlement/billing/fulfillment path; `PARTIAL_ALIVE` only for lower-layer services reused by that future path.

Do not call ggen SaaS `ALIVE` merely because `/provision` and `/packs` work.

## What SaaS means here

A SaaS capability hides implementation/toolchain concerns behind a buyer-facing contract:

```text
identity/subscription
  -> entitlement
  -> capability selection
  -> purchase/order
  -> trust/authority admission
  -> fulfillment
  -> delivered artifact
  -> actuation/derivation receipts as applicable
  -> metering/billing record
  -> independent verification/replay
```

The buyer should not need to author TTL/SPARQL/ggen configuration merely to consume a prequalified capability.

## What exists in v26.8.18

Lower-layer prerequisites are real:

- `POST /provision` executes real ggen manufacture and returns receipt verification data;
- runs are tenant/project scoped at namespace/workspace level;
- ggen-marketplace exposes a real registry/query bridge;
- the observed bridge returned 151 pack metadata records;
- signed/expiring storage URL primitives exist elsewhere in platform-console;
- audit, cost and quota mechanisms exist as platform primitives.

These are composable ingredients, not a finished SaaS state machine.

## What is missing

### 1. Subscription/entitlement identity

No current ggen request proves a buyer subscription and maps it to an admitted capability set.

### 2. Purchase/order state

There is no canonical purchase/order object with lifecycle such as requested -> admitted -> paid/authorized -> fulfilled/refused -> delivered -> verified.

### 3. Trust-tier-aware buyer admission

Pack trust mechanisms exist, but the current HTTP provisioning surface does not bind caller entitlement/subscription tier to a hard pack/capability admission rule.

### 4. Receipt-tied metering

Usage must derive from the actual fulfilled/receipted invocation, not a driftable parallel counter. No complete receipt -> usage -> bill relation currently exists.

### 5. Billing/settlement

There is no closed price, invoice/charge, settlement, refund/credit or external billing integration for ggen capabilities.

### 6. Durable tenant delivery

`/provision` may return artifact contents, but a SaaS delivery contract needs durable tenant-scoped artifact custody and bounded delivery (for example signed expiring URLs) with identity/revocation evidence.

### 7. Fulfillment actuation receipt

A generated artifact receipt proves manufacture. If fulfillment also deploys/changes an external buyer environment, that consequential transition requires its own admitted BRCE path and actuation receipt. Derivation receipt != actuation receipt.

## Marketplace semantics

A listed pack is a capability candidate/catalog record. It is not automatically:

- purchasable;
- compatible with the buyer context;
- authorized for the buyer;
- `ALIVE` on the buyer's target;
- class-closed;
- deployable without additional admission.

The SaaS catalog should surface standing/evidence and refuse unsupported combinations rather than flattening every record into “available.”

## Proposed minimum state machine

```text
DISCOVERED
  -> SELECTED
  -> ENTITLEMENT_CHECKED
  -> ADMITTED | REFUSED
  -> FULFILLING
  -> MANUFACTURED
  -> [optional external DO via BRCE]
  -> DELIVERED
  -> VERIFIED
  -> METERED
```

Failures/timeouts need explicit states such as `FAILED`, `AMBIGUOUS`, `REFUSED`, `BLOCKED`, not generic success/error text.

## Required receipts

At minimum distinguish:

- selection/entitlement evidence;
- manufacturing/derivation receipt;
- external actuation receipt where the buyer environment changes;
- delivery identity/digest;
- metering/billing event identity.

One receipt type should not be overloaded to pretend all five transitions are identical.

## Definition of Done

A future `ggen_saas` rail can become `ALIVE` only when a real end-to-end buyer fixture executes:

1. buyer authenticates;
2. entitlement is verified;
3. one catalog capability is selected;
4. unauthorized tier negative fixture refuses;
5. authorized purchase/order is persisted;
6. real ggen manufacture executes;
7. artifact/receipt is durably delivered;
8. any external deployment goes through BRCE;
9. usage is derived from the fulfilled receipt;
10. the buyer independently verifies delivered identity/receipt;
11. replay reproduces the bounded fulfillment result.

## Falsifiers

The SaaS claim is invalid if `/provision` is equated with purchase, pack listing is equated with entitlement, billing can diverge from fulfilled receipt identity, or a buyer-triggered deployment bypasses the authority/actuation-receipt boundary.

## See also

- [01 — ggen as IaaS](01-GGEN-AS-IAAS.md)
- [02 — ggen as PaaS](02-GGEN-AS-PAAS.md)
- [04 — BRCE cross-cutting](04-GGEN-BRCE-CROSS-CUTTING.md)
- [`../../GGEN-SERVICE.md`](../../GGEN-SERVICE.md)
