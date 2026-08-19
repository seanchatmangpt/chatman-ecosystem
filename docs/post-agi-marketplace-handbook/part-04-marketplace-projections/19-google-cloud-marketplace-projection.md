# 19. Google Cloud Marketplace Projection

> **Vendor observation date:** 2026-08-19. Re-verify Cloud Commerce Partner Procurement and Kubernetes application requirements before implementation.

## Two important Google projections

Google Cloud Marketplace can represent the platform commercially as SaaS and technically as a Kubernetes application. Those rails share canonical product identity but have different contracts and qualification criteria.

## SaaS procurement

Cloud Commerce Partner Procurement models commercial customer state with resources such as Accounts and Entitlements. Lifecycle notifications can be delivered through configured notification channels such as Pub/Sub.

The safe architecture is:

```text
Google procurement notification
  → admit source + event
  → reconcile with Procurement API state
  → map Account to canonical Organization
  → map Entitlement to canonical Agreement/Entitlement event
  → shared entitlement transition
  → receipt
```

Pub/Sub delivery proves that a message arrived. It does not replace authoritative state reconciliation where the API contract requires or permits it.

## Usage reporting

Where the selected Google commercial model requires Service Control or related usage reporting, the client projects canonical meter batches. It does not own usage aggregation.

```text
Observed usage
  → canonical frozen MeterBatch
  → Google usage/report projection
  → vendor acceptance observation
  → metering receipt
```

## Producer admission

Producer Portal, partner/vendor application, payments setup, and product review are external admissions. A repository can prepare a complete product package while publication remains `BLOCKED:EXTERNAL_VENDOR_REVIEW`.

## Kubernetes application packaging

Google's Kubernetes application path has packaging rules around application metadata, images, resource APIs, and an `Application` custom resource. Marketplace validation can be stricter than what a normal cluster accepts.

That creates an important boundary: a package must not silently remove a security or operational control merely to satisfy a listing validator. If a required resource uses a marketplace-disallowed API generation and no equivalent exists, the projection is BLOCKED or needs an explicitly admitted alternate architecture.

```text
CanonicalDeployment
  → GCP Kubernetes projection
  → marketplace validator
  → execute in admitted target
  → verify product invariants
```

## Identity

A Google billing/account resource is a marketplace identity. Customer runtime tenancy and human authentication remain separate. The canonical organization binds them through evidence rather than equality.

## Refusals

- `REFUSED:PUBSUB_MESSAGE_AS_UNRECONCILED_ENTITLEMENT_TRUTH`
- `REFUSED:GOOGLE_ACCOUNT_AS_CANONICAL_ENTERPRISE`
- `REFUSED:ALPHA_RESOURCE_SILENTLY_ACCEPTED`
- `REFUSED:SECURITY_CONTROL_DROPPED_FOR_PACKAGING`
- `REFUSED:SIMULATED_GCP_AS_LIVE_GCP`

## Operational exercise

Generate two projections from one canonical product: SaaS procurement/entitlement and a Kubernetes application package. Record which invariants are shared, which facts are Google extensions, and which qualification evidence is independent. A Kubernetes package success must not be used as evidence for SaaS entitlement, or vice versa.
