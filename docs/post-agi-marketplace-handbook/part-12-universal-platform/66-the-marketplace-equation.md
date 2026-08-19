# 66. The Marketplace Equation

## From manufacture to commerce

The Chatman Equation begins with admitted observation:

```text
A = μ(O*)
R = receipt(A)
```

Marketplace engineering adds a projection and an explicit consequential boundary.

```text
G_c = μ(O*)
C_m = π_m(G_c)
Intent = CONSTRUCT(C_m, requested_transition)
(A, R) = BRCE(Intent, Authority*)
S = standing(A, R, replay, exclusions)
```

The equations are types, not slogans. They prevent the product graph, projection, intent, authority, consequence, and evidence from being collapsed into one “automation” function.

## `O`

Observations include platform capabilities, marketplace documentation/API contracts, customer requirements, commercial plans, security evidence, legal approvals, seller/account state, and runtime facts.

They are partial and can be stale.

## `O*`

Admission aligns exact subject, source, freshness, authority relevance, constraints, and semantic mapping. Unknown facts remain outside rather than being filled by model confidence.

## `μ`

Manufacture constructs canonical commercial knowledge and artifacts: ontology, product graph, plans, mappings, adapters, packages, tests, listing projections, and evidence views.

`ggen` is a concrete manufacturing engine. Formal admission and validation constrain its outputs.

## `π_m`

Projection renders the canonical product into a specific marketplace. Projection is allowed to add vendor extensions or expose narrower capability, but must not silently change product identity or rights.

## BRCE

Commercial DO begins only after an immutable intent is admitted against exact authority.

```text
Broker.DO(Intent, Authority*) → Consequence
Verify(Consequence)
Receipt(...)
```

The receipt binds what happened; it does not become authority for replay.

## Standing

Standing is the final evidence claim and remains scoped:

```text
S = (subject, capability, status, evidence, exclusions, falsifier)
```

A successful generated AWS adapter does not imply an AWS sale. An AWS sale does not imply Oracle support. A marketplace seller approval does not imply entitlement code works.

## Product invariant

For an invariant `I` and admitted market projection:

```text
I(G_c) = I(normalize(π_m(G_c)))
```

where the invariant applies. If it cannot hold, the projection has a typed loss or is unsupported.

## Refusals

- `REFUSED:O_AND_O_STAR_COLLAPSED`
- `REFUSED:PROJECTION_CHANGES_CANONICAL_IDENTITY`
- `REFUSED:MANUFACTURE_AS_AUTHORITY`
- `REFUSED:RECEIPT_AS_AUTHORITY`
- `REFUSED:EVIDENCE_FROM_DIFFERENT_SUBJECT`

## Operational exercise

Write the complete equation for creating a SaaS private offer, observing buyer acceptance, activating entitlement, fulfilling a tenant, submitting first usage, and reconciling settlement. Mark every transition where the type changes and the exact point where DO authority is required.
