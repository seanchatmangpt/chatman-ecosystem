# 37. Marketplace versus Direct Sales

## Route is not product identity

Direct sales and marketplace sales are commercial routes over the same canonical product. A buyer may choose a marketplace because the cloud vendor is already approved, the transaction can fit an existing procurement process, or committed cloud spend is relevant. Another buyer may prefer a direct agreement because its terms, billing, or regional requirements do not fit a marketplace projection.

The product should not fork because the route changes.

```text
CanonicalProduct
  ├── DirectAgreement projection
  ├── AWS agreement projection
  ├── Microsoft agreement projection
  └── Channel/private-offer projection
```

Entitlement normalizes all admitted routes into the same rights model.

## Route selection

Treat route selection as SELECT over constraints:

```text
Route* = argmax admissible(Value - Friction - Cost)
```

Inputs include buyer procurement preference, marketplace eligibility, term expressiveness, private-offer capability, cloud-commit strategy, legal fit, channel participation, transaction fees, seller operations, settlement timing, and regional availability.

The system can recommend. The buyer and seller authorities decide.

## One agreement, one charging authority

The most important invariant is preventing duplicate billing. A direct Stripe invoice and an AWS Marketplace meter must not both charge for the same right and period unless the agreement explicitly defines distinct products/charges.

The canonical agreement therefore records its active billing route and pricing projection.

```text
Agreement
  → BillingRoute
  → Meter/Invoice projection
```

Changing route is a commercial migration requiring effective time and receipts, not a configuration toggle.

## Cloud commitments are buyer facts

Marketplace purchase can sometimes help a buyer consume committed cloud spend, but applicability is customer-, vendor-, program-, and agreement-specific. Do not put “uses your commit” into universal product semantics. It belongs to the selected route and the buyer's admitted procurement facts.

## Direct remains useful

Direct routes can support buyers or terms a marketplace cannot express, early pilots before seller approval, bespoke invoicing, or jurisdictions where the target market is unavailable. Direct does not mean ungoverned: it still needs agreement, entitlement, metering, billing, settlement, support, and receipts.

## Refusals

- `REFUSED:MARKETPLACE_AND_DIRECT_DOUBLE_BILLING`
- `REFUSED:CLOUD_COMMIT_ASSUMED_WITHOUT_BUYER_EVIDENCE`
- `REFUSED:ROUTE_CHANGE_AS_RUNTIME_TOGGLE`
- `REFUSED:ROUTE_SPECIFIC_PRODUCT_FORK`
- `REFUSED:DIRECT_AS_NO_ENTITLEMENT_REQUIRED`

## Operational exercise

Route three enterprise deals: one buyer with cloud commitment and marketplace preference, one requiring terms the marketplace cannot represent, and one already approved as a direct vendor. For each, preserve the same product/plan identity and show the agreement, entitlement, billing route, settlement, renewal, and migration policy.
