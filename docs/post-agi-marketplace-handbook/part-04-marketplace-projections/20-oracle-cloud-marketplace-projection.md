# 20. Oracle Cloud Marketplace Projection

> **Vendor observation date:** 2026-08-19. Re-verify Oracle Cloud Marketplace partner, transaction, and metering requirements before implementation.

## Oracle is not an AWS-shaped target

Oracle Cloud Marketplace provides its own listing, pricing, transaction, private-offer, SaaS, and OCI deployment surfaces. The correct architecture maps those surfaces into the canonical graph rather than asking how to make Oracle behave like AWS.

Canonical objects remain product, plan, offer, agreement, entitlement, fulfillment, usage, settlement, and evidence. Oracle listing IDs, SKUs, meters, package identifiers, and account identifiers are mappings.

## SaaS and OCI deployment are separate rails

A SaaS product may be delivered and operated by the seller while Oracle participates in marketplace discovery, commercial transaction, and payment. An OCI application or deployment artifact can instead provision into Oracle infrastructure.

```text
CanonicalProduct
  ├── SaaS projection → seller-hosted fulfillment
  └── OCI deployment projection → OCI target fulfillment
```

The existence of one does not prove the other.

## Listing, SKU, and meter

Oracle documentation distinguishes listing identity, SKU-like commercial configuration, pricing/meter definitions, and transaction behavior. The canonical graph should bind each Oracle object to the exact product version and plan it projects.

Usage-based reporting must consume the same canonical `MeterBatch` abstraction used for other markets. Oracle-specific units and reporting intervals belong to the projection. If the vendor's billing model cannot express a canonical pricing rule, the mapping becomes `LOSSY` or `UNSUPPORTED`; the meter definition is not silently altered.

## Private offers

Buyer-specific terms should be represented as admitted deltas from a canonical plan, then rendered into Oracle's supported private-offer process.

```text
CanonicalPlan + BuyerScopedDelta
  → Oracle Private Offer
  → accepted transaction/agreement
  → canonical Agreement
  → Entitlement
```

The buyer's Oracle account identity maps to the canonical organization. It is not the organization itself.

## Payment and reconciliation

Where Oracle bills and collects through the marketplace, settlement records must be reconciled against canonical agreement, usage, fees, credits, and payout data. The fact that Oracle collected money does not establish runtime fulfillment; the fulfillment plane independently verifies service availability.

## Partner and publication standing

Partner enrollment, seller verification, listing approval, and any required product review are external admission gates. Generated listing metadata can be `CANDIDATE` while seller status is `BLOCKED`.

## Refusals

- `REFUSED:ORACLE_LISTING_ID_AS_CANONICAL_PRODUCT`
- `REFUSED:OCI_DEPLOYMENT_AS_SAAS_ENTITLEMENT`
- `REFUSED:BYOL_RIGHT_AS_MARKETPLACE_NATIVE_RIGHT`
- `REFUSED:UNMAPPED_ORACLE_METER_SEMANTIC`
- `REFUSED:SETTLEMENT_AS_FULFILLMENT`

## Operational exercise

Project one canonical platform into two Oracle forms: seller-operated SaaS and an OCI-deployed application. For each, map product/plan identity, buyer identity, entitlement, fulfillment, meter, private offer, settlement, support, and exact qualification evidence.
