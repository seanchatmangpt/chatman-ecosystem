# 59. Product Lifecycle at Marketplace Scale

## Commercial history outlives a deployment

Marketplace products evolve across code versions, plans, prices, package formats, API generations, certifications, support promises, and marketplace policies. Customers can remain under agreements negotiated years earlier.

Lifecycle engineering therefore preserves historical semantics while manufacturing new projections.

```text
ProductVersion_n
  → projections_n
  → agreements_n*

ProductVersion_n+1
  → projections_n+1
  → migration offers
```

The new version does not rewrite the old agreements.

## Version every semantic that can affect a customer

Relevant version identities include:

```text
product version
plan version
pricing version
meter definition
entitlement transition contract
marketplace adapter/pack
vendor API observation
container/package digest
security certification
support/SLA policy
legal terms
```

A product release can reuse an unchanged plan or meter version. The important property is explicit correspondence.

## Deprecation is a product capability

A deprecation policy states notice, supported versions, migration path, final support date, data export, and customer obligations. Marketplace listings and docs project that policy.

An API deprecation from a marketplace vendor creates a reverse dependency: the product may need an adapter migration even when its own runtime has not changed.

## Coexistence is normal

A three-year enterprise agreement can require price/meter semantics that are no longer offered publicly. The control plane may need to support legacy agreement evaluation while all new buyers receive the current plan.

Do not solve this by keeping an unbounded number of code forks. Keep versioned commercial semantics and migrate through explicit transitions.

## Certification correspondence

A new image digest, Salesforce package, ServiceNow scoped app, Red Hat certified container, or managed-application package can invalidate prior artifact evidence. The release graph should show which certification/review applies to which exact artifact.

## End of life

EOL can require offer withdrawal, renewal refusal, migration, data export, entitlement termination, support window, marketplace listing updates, and settlement closure. These are separate transitions with receipts.

## Refusals

- `REFUSED:OLD_PLAN_MUTATED_IN_PLACE`
- `REFUSED:NEW_ARTIFACT_UNDER_STALE_CERTIFICATION`
- `REFUSED:VENDOR_API_DEPRECATION_IGNORED`
- `REFUSED:SUPPORT_ENDED_BEFORE_AGREEMENT_TERM`
- `REFUSED:EOL_AS_DELETE_LISTING_ONLY`

## Operational exercise

Plan a breaking meter-definition change while multi-year agreements remain active. Show how old and new meter/price versions coexist, how new listings are generated, how customers migrate, how settlement is reconciled during transition, and what evidence retires the old path.
