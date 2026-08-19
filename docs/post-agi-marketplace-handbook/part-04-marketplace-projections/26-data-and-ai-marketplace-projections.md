# 26. Data and AI Marketplace Projections

> **Vendor observation date:** 2026-08-19. Snowflake and Databricks marketplace capabilities change rapidly; re-verify provider, listing, sharing, pricing, and monetization rules.

## The thing sold may not be an application

Data and AI marketplaces commercialize governed access to data, models, notebooks, applications, shares, functions, or other analytic assets. The commercial right can therefore be “may query this governed dataset” rather than “may run this service.”

That changes the entitlement and fulfillment objects without changing the canonical calculus.

```text
Agreement
  → Entitlement
  → Data/Model/Application Access
  → Usage observation
  → Marketplace pricing/settlement
```

## Snowflake projection

Snowflake supports public and private listings and provider profiles. Current monetization documentation includes paid-listing pricing models such as usage-based and subscription structures, with separate eligibility/operational requirements for monetization.

The canonical product maps Snowflake listing, share/application identity, consumer identity, pricing model, trial, and usage dimension explicitly. Provider-profile approval is not product runtime evidence.

A data listing also carries rights beyond availability: allowed consumers, regional availability, sample/trial behavior, data freshness, downstream-use terms, privacy, and revocation.

## Databricks projection

Databricks Marketplace uses provider listings and governed sharing/access mechanisms for data and AI assets. Private exchanges and request/approval flows demonstrate that discoverability and entitlement are separate states.

Canonical identity should bind listing/share/model/application identifiers to one product version while preserving consumer workspace/metastore identities as tenant projections.

## AI model economics

Tokens are only one possible unit. Models can be priced by request, compute, provisioned capacity, model unit, application subscription, data access, or outcome. The canonical meter must describe the product's economic quantity, then map into the marketplace's supported model.

## Governance is part of fulfillment

For a data product, fulfillment includes access policy, share grants, region, object set, lineage, and revocation—not just successful deployment. A security or privacy restriction lost during projection is a commercial defect.

## Public versus private markets

Private listings/exchanges can expose selected products only to invited consumers. That visibility boundary is a commercial control. It should be represented in the offer/listing graph rather than implemented as marketing convention.

## Refusals

- `REFUSED:DATA_ACCESS_AS_SOFTWARE_INSTALL`
- `REFUSED:MODEL_TOKEN_AS_UNIVERSAL_METER`
- `REFUSED:PRIVATE_LISTING_AS_PUBLIC_DISCOVERY`
- `REFUSED:PROVIDER_PROFILE_AS_PRODUCT_STANDING`
- `REFUSED:GOVERNANCE_POLICY_DROPPED_IN_PROJECTION`

## Operational exercise

Express one analytics platform capability as a Snowflake listing and a Databricks Marketplace listing. Model provider identity, consumer identity, entitlement, share/application fulfillment, trial, usage, governance, revocation, and settlement. Record every semantic that does not map cleanly between the two markets.
