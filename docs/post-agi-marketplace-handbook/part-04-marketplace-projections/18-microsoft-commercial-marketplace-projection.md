# 18. Microsoft Commercial Marketplace Projection

> **Vendor observation date:** 2026-08-19. This chapter follows current Microsoft Learn SaaS Fulfillment v2 and Partner Center guidance; re-verify before publication.

## Separate commercial service identity from customer login identity

Microsoft's commercial marketplace SaaS integration requires a publisher backend to authenticate to marketplace APIs. That service-to-service identity is not the same question as how customers authenticate to the SaaS product.

This distinction corrects a common architectural error: treating a Microsoft Entra application used for Marketplace API calls as proof that the customer-facing application must use Entra SSO. Marketplace does not require that equivalence.

## Offer and plan projection

Partner Center represents transactable SaaS through offers and plans with vendor-defined pricing constraints. The canonical graph owns product and plan semantics; Partner Center IDs map to them.

```text
CanonicalProduct/Plan
  → Microsoft Offer/Plan
  → purchase
  → SaaS subscription observation
  → canonical Agreement/Entitlement
```

Pricing-model choices and metered dimensions are Microsoft projection constraints. Do not change canonical meter meaning to fit a field silently.

## SaaS Fulfillment APIs v2

Current Microsoft guidance uses SaaS Fulfillment APIs v2 for transactable SaaS lifecycle integration; v1 is deprecated. The backend service authenticates and handles subscription lifecycle operations under the vendor protocol.

A typical path is:

```text
purchase/landing observation
  → resolve subscription when required
  → activate according to the admitted flow
  → process subscription changes idempotently
  → shared entitlement state machine
  → fulfillment + verification
```

Where Microsoft supports automatic activation paths, the projection should represent that explicitly rather than forcing a manual `Resolve` assumption onto every offer.

## Metered billing

Marketplace metered billing reports declared custom dimensions. The canonical meter still owns observation, aggregation, deduplication, effective plan, and correction semantics. The Microsoft client only projects frozen batches into Marketplace's accepted wire model.

## Managed-application projection

If the product is also distributed as a managed application or Kubernetes-oriented package, treat that as a separate fulfillment projection. Package validation and deployment success do not prove SaaS subscription standing.

## Development and production

Use separate product/offer environments where the marketplace workflow supports them, and bind every test receipt to the exact offer/plan IDs. Evidence from a development offer does not automatically transfer to production.

## Refusals

- `REFUSED:MARKETPLACE_SERVICE_ID_AS_END_USER_IDP_REQUIREMENT`
- `REFUSED:FULFILLMENT_V1_FOR_NEW_INTEGRATION`
- `REFUSED:PLAN_ID_AS_CANONICAL_PLAN`
- `REFUSED:METER_CLIENT_AS_USAGE_SOURCE`
- `REFUSED:DEV_OFFER_EVIDENCE_AS_PRODUCTION_STANDING`

## Operational exercise

Model a Microsoft transactable SaaS purchase with publisher service authentication, subscription activation, lifecycle change, metered dimension, and customer SSO through a separate enterprise IdP. Prove that commercial service identity, organization identity, tenant identity, and human principals remain distinct.
