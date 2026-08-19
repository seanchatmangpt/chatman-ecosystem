# 14. Pricing

## Pricing is executable commercial policy

A number in a vendor console is not a complete price. Price semantics include currency, unit, quantity, tier, term, eligibility, discounts, commitments, credits, effective time, renewal behavior, and the marketplace projection capable of expressing them.

```text
Price = f(unit, quantity, tier, term, currency,
          eligibility, effective_time, negotiated_delta)
```

The canonical product graph owns those semantics. Marketplace forms render them under vendor-specific constraints.

## Separate price from measured quantity

Metering answers how much was consumed. Pricing answers what that admitted quantity costs under the effective agreement. This separation allows the same usage events to support public list price, enterprise committed spend, negotiated private offers, and future price versions without rewriting evidence.

## Common models

### Flat subscription

A fixed amount grants a plan for a term. The contract still needs quantity and scope semantics if limits exist.

### Per-seat

The difficult object is `seat`: named user, active user, provisioned identity, peak concurrent user, or some other admitted quantity. Pricing cannot be more precise than identity policy.

### Usage-based

The price applies to one or more measured dimensions. Unit and window semantics must bind to the meter definition.

### Tiered or graduated

Tiers require exact boundary behavior, aggregation window, and whether rates apply to all units or only units within each band.

### Committed spend and credits

Commitment adds a contract-level balance and consumption policy. Credits need source, expiry, scope, and application order.

### Hybrid

A base subscription plus overage is common for enterprise platforms. It is still one canonical plan if the product rights and meter relationships are explicit.

## Projection constraints

Different marketplaces support different pricing families and mutation rules. A canonical model should be richer than any one vendor but must refuse a projection it cannot express faithfully. The right outcome is `UNSUPPORTED` or a deliberately narrower offer, not a hidden transformation.

Microsoft, for example, constrains SaaS offer pricing models and custom metered dimensions; AWS offer/amendment behavior varies by product/pricing class; data marketplaces can expose pricing primitives centered on queries or data consumption. These are projection rules.

## Effective price is immutable history

When list price changes, existing agreements continue under their admitted terms until a lawful renewal/amendment says otherwise. Never recalculate historical usage using today's price table.

## Refusals

- `REFUSED:VENDOR_CONSOLE_AS_PRICE_SOURCE`
- `REFUSED:UNDEFINED_BILLING_UNIT`
- `REFUSED:RETROACTIVE_PRICE_REWRITE`
- `REFUSED:UNREPRESENTABLE_VENDOR_PRICE_MODEL`
- `REFUSED:DISCOUNT_WITHOUT_BUYER_SCOPE`

## Operational exercise

Price one platform as flat subscription, per-seat, metered usage, committed spend, and hybrid subscription-plus-overage. For each model define the exact meter, entitlement relationship, effective-time policy, private-offer delta, vendor projection constraints, and unit-economics falsifier.
