# 17. Amazon Web Services Marketplace Projection

> **Vendor observation date:** 2026-08-19. Re-verify AWS Marketplace contracts before implementation or publication.

## AWS is a projection, not the product core

AWS Marketplace exposes several distinct commercial and delivery surfaces: SaaS products, contract and usage pricing, private offers and agreements, Marketplace Metering, Entitlement Service, and container distribution. The canonical platform should map those primitives rather than adopting AWS vocabulary as universal commerce.

## SaaS customer resolution

AWS SaaS registration begins from an AWS Marketplace purchase context and `ResolveCustomer`. Current AWS documentation for new SaaS integrations emphasizes `CustomerAWSAccountId` and `LicenseArn`; a new implementation should not build durable customer identity around the older `CustomerIdentifier` field.

The flow is:

```text
AWS purchase registration observation
  → ResolveCustomer
  → map AWS account/license to canonical Organization + Agreement
  → admit canonical entitlement event
  → shared entitlement transition
  → fulfillment
  → receipt
```

The AWS account is a marketplace identity mapping, not the enterprise itself.

## Entitlement and metering

Depending on the SaaS pricing model, the AWS integration can involve Marketplace Entitlement Service and Marketplace Metering operations such as `GetEntitlements` and `BatchMeterUsage`. Those are wire projections over canonical entitlement and meter batches.

`BatchMeterUsage` must consume frozen, deduplicated, agreement-bound usage. It should never calculate product usage inside the AWS client. An ambiguous network result after submission is a financial uncertainty requiring observation/idempotency, not a blind retry.

## Offers and agreements

AWS private offers can express buyer-scoped commercial terms and custom legal content. The canonical representation remains:

```text
CanonicalPlan + BuyerScopedDelta
  → AWS private-offer projection
  → buyer acceptance
  → AWS agreement observation
  → canonical Agreement
```

Amendment capabilities differ across SaaS pricing/product classes. Model those as AWS projection rules rather than assuming every agreement has the same mutation surface.

## Container products

Container publication is an artifact-distribution rail. The exact image digest, scanning/certification evidence, Marketplace-owned repository requirements where applicable, deployment documentation, and product-version mapping must be retained.

Container publication does not by itself prove SaaS entitlement, metering, or a customer sale.

## Seller and partner admission

Tax, banking, seller registration, product review, FTR/partner-program outcomes, and co-sell eligibility are external admissions. Engineering can generate evidence and submission artifacts; it cannot truthfully mark those gates complete until AWS does.

## Refusals

- `REFUSED:LEGACY_CUSTOMER_IDENTIFIER_AS_NEW_CANONICAL_ID`
- `REFUSED:AWS_EVENT_AS_DIRECT_FEATURE_AUTHORITY`
- `REFUSED:USAGE_COMPUTED_INSIDE_METER_CLIENT`
- `REFUSED:AMBIGUOUS_BATCH_RETRY`
- `REFUSED:CONTAINER_LISTING_AS_SAAS_STANDING`
- `REFUSED:FTR_FROM_LOCAL_TESTS`

## Qualification

Qualify independently:

1. customer resolution;
2. entitlement transition;
3. meter submission and reconciliation;
4. private offer/agreement mapping;
5. container artifact publication;
6. exact deployed runtime;
7. seller/review state.

One green rail does not crown AWS Marketplace globally.

## Operational exercise

Build an AWS projection manifest mapping canonical product, plan, organization, agreement, entitlement, meter, private offer, container artifact, and receipt to AWS identifiers and APIs. Include `UNKNOWN` for every mapping that has not been executed against the exact AWS environment.
