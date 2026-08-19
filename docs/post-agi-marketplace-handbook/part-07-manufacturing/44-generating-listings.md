# 44. Generating Listings

## Listing metadata is a projection

Marketplace titles, descriptions, categories, plans, prices, screenshots, support contacts, legal links, technical metadata, and search terms should derive from admitted product facts plus marketplace content rules.

```text
Listing_m = π_m(ProductGraph, ContentPolicy_m)
```

A listing is therefore a generated view, not a new source of product truth.

## Claims must be grounded

Marketing text is consequential even when it does not call an API. A claim such as “customer-managed keys,” “99.99% availability,” “deploys air-gapped,” or “available in all regions” creates procurement expectations and can become contractual context.

The listing generator should select claims from canonical `Capability`, `SecurityClaim`, `DeploymentClass`, and `SupportPolicy` objects with admitted standing. It must refuse unsupported superlatives.

## Plans and pricing

Plan names can differ across marketplaces, but mapping must remain explicit. The generated listing carries canonical plan ID/version in machine metadata or the accompanying projection manifest even if the public display name changes.

Pricing generation uses the effective canonical pricing policy and vendor-supported model. If the market cannot represent the plan faithfully, generation produces a gap instead of changing economics silently.

## Legal and support metadata

EULA, privacy, support, refund, DPA, and other legal/support links should reference approved artifacts with version/digest. The generator can enforce required presence and marketplace formatting; it cannot approve the content.

Support contacts need ownership and lifecycle. A stale email or documentation URL is a production commercial defect even if the application runtime is healthy.

## Media assets

Screenshots, diagrams, logos, and videos need rights, version relevance, accessibility/format constraints, and product consistency. Treat them as versioned listing assets rather than files copied between portals.

## Drift detection

Compare generated projection with currently published vendor state. A discrepancy can be:

```text
expected manual vendor field
out-of-band authorized change
stale published projection
vendor-normalized representation
UNKNOWN drift
```

Do not automatically overwrite unknown drift. Observe and classify first.

## Refusals

- `REFUSED:UNGROUNDED_MARKETING_CLAIM`
- `REFUSED:STALE_SUPPORT_METADATA`
- `REFUSED:PLAN_MAPPING_MISSING`
- `REFUSED:GENERATED_LEGAL_APPROVAL`
- `REFUSED:UNREPRESENTABLE_PRICE_SILENTLY_CHANGED`
- `REFUSED:UNKNOWN_VENDOR_DRIFT_AUTOCORRECTED`

## Operational exercise

Generate listing candidates for AWS, Microsoft, Google, Oracle, and Alibaba from one product graph. Intentionally add an unsupported security claim and an unapproved EULA draft. The listing admission gate must refuse both while still producing reversible valid projections for unaffected fields.
