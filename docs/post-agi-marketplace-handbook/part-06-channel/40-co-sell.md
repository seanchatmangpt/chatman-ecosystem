# 40. Co-Sell

## Distribution and sales motion are different systems

Marketplace distribution makes a product discoverable and transactable. Co-sell coordinates seller and platform/vendor sales organizations around opportunities. The systems should share product identity and evidence while keeping opportunity state separate from commercial authority.

```text
Opportunity != Offer != Agreement != Entitlement
```

That inequality is the central safety rule.

## Opportunity graph

Useful co-sell objects include:

```text
PartnerProgram
EligibleProduct
Opportunity
AccountMapping
Referral
SalesPlay
TechnicalValidation
JointSolution
Attribution
```

They link to the canonical product and customer organization but do not create customer rights.

## Product eligibility

Different cloud and enterprise vendors have different partner, validation, revenue, certification, and marketplace prerequisites for co-sell. Eligibility is therefore a marketplace-specific standing claim.

A product listed in a marketplace can remain `UNKNOWN` for co-sell until the partner program admits it. Conversely, an eligible partner solution may not yet have executed a customer marketplace transaction.

## Account mapping and privacy

Co-sell can involve sharing opportunity/customer information. The system should represent what data is permitted to cross the partner boundary, under which authority, and for which purpose. “The vendor is our partner” is not a data-sharing policy.

## From opportunity to commerce

The safe transition is:

```text
Opportunity
  → approved sales action
  → public/private offer candidate
  → offer publication DO
  → buyer acceptance
  → Agreement
  → Entitlement
```

Every arrow changes semantic type. CRM stage changes do not skip them.

## Technical validation

Architecture diagrams, security evidence, sandbox results, and marketplace qualification can support the opportunity. They should be exact-subject evidence reusable from the product graph, not bespoke PowerPoint claims that drift from runtime.

## Measurement

Co-sell metrics can include sourced/influenced pipeline, acceptance rate, sales cycle, marketplace conversion, renewal, partner attribution, and product/region coverage. Keep forecasts separate from realized agreements and settlement.

## Refusals

- `REFUSED:CRM_STAGE_AS_CONTRACT`
- `REFUSED:COSELL_ELIGIBILITY_FROM_LISTING_ALONE`
- `REFUSED:PARTNER_RELATIONSHIP_AS_CUSTOMER_DATA_AUTHORITY`
- `REFUSED:OPPORTUNITY_AS_FULFILLMENT_TRIGGER`
- `REFUSED:FORECAST_AS_REVENUE_RECEIPT`

## Operational exercise

Take one joint cloud-vendor opportunity from account mapping through technical validation, private offer, acceptance, entitlement, fulfillment, and revenue attribution. Put a hard authority fence between every sales object and every commercial or runtime DO.
