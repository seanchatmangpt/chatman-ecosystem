# 2. Platform as a Commercial Product

## Thesis

An internal platform becomes a commercial product only when its capabilities are wrapped in stable external promises: identity, plans, rights, lifecycle, support, security, deployment responsibility, and economic terms. Adding a price to an internal platform does not complete that transformation.

Platform-as-a-product inside an enterprise optimizes developer experience. A commercial platform must additionally survive organizational boundaries. The buyer cannot rely on tribal knowledge about what a plan means or which deployment is supported. Every promise must be versioned and attributable.

## Canonical identity before SKU identity

The root object is `CommercialProduct`, not an AWS product code, Microsoft offer ID, Google listing, Salesforce package, or SAP solution identifier.

```text
CommercialProduct
  ├── ProductVersion*
  ├── Capability*
  ├── Plan*
  ├── DeploymentClass*
  ├── SupportPolicy*
  ├── SecurityClaim*
  └── LifecyclePolicy
```

A marketplace SKU is a projection of one plan or product variant. It can be replaced without changing the canonical product. Conversely, changing a marketplace SKU must not silently change the underlying rights.

The same separation applies to technical artifacts. Container digests, Helm charts, Operators, managed applications, SaaS endpoints, and data shares are fulfillment artifacts. They bind to product versions but are not themselves the product identity.

## Capability versus packaging

A capability answers what the customer can receive. A plan answers which capabilities and quantities are commercially granted. An offer adds buyer-scoped terms. An agreement records accepted terms. Entitlement represents currently effective rights.

This ordering prevents a common failure: using runtime feature flags as the commercial source of truth. Runtime flags should be derived from admitted entitlement, not from a marketplace webhook or manually edited plan name.

## Promises become architecture

External promises have implementation consequences:

- a 99.99% SLA requires measurable availability and sufficient architecture;
- customer-managed keys require a real key boundary and lifecycle;
- private connectivity requires a supported network topology;
- regional residency constrains deployment and telemetry;
- a three-year contract constrains deprecation and migration;
- per-seat pricing requires a defensible seat identity and counting policy;
- usage pricing requires an exact meter and correction policy;
- premium support requires severity, response, escalation, and evidence semantics.

The product graph therefore owns the promise before a listing generator renders marketing text.

## Commercial lifecycle

```text
DRAFT → ADMITTED → LISTED → OFFERED → AGREED
      → ENTITLED → FULFILLED → OPERATING
      → RENEWED | AMENDED | TERMINATED
```

The arrows are not one state machine in implementation; they are a conceptual dependency graph. Listing approval can be BLOCKED while the canonical product remains admitted. An agreement can be active while fulfillment is PARTIAL_ALIVE. A product can be ALIVE on one marketplace and UNKNOWN on another.

## Typed exclusions

- `REFUSED:SKU_AS_CANONICAL_IDENTITY`
- `REFUSED:TECHNICAL_ARTIFACT_AS_PRODUCT`
- `REFUSED:UNVERSIONED_COMMERCIAL_PROMISE`
- `REFUSED:RUNTIME_FLAG_AS_ENTITLEMENT_AUTHORITY`
- `REFUSED:CUSTOMER_FORK_WITHOUT_OFFER_MODEL`

A bespoke enterprise term should become an explicit buyer-scoped offer or policy delta, not an untraceable fork of code and semantics.

## Operational exercise

Create a canonical record for the running platform without mentioning a marketplace. Include product/version identity, capabilities, plans, deployment classes, support tiers, security claims, metering dimensions, lifecycle rules, and explicit non-goals. Only after the record is admitted should you map it into vendor SKUs.
