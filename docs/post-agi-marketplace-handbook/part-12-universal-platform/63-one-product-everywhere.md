# 63. One Product Everywhere

## Invariant identity, plural projections

“One product everywhere” does not mean identical marketplace listings, APIs, pricing forms, or deployment packages. It means a canonical product/version can be identified across every admitted projection and customer rights remain explainably related.

```text
Identity(Product) invariant under admitted π_m
```

AWS can assign one product code, Microsoft another offer ID, Salesforce a package/version, SAP a solution identity, and Alibaba a product/SKU. Those identifiers are mappings.

## Projection identity

Each `MarketplaceProjection` should bind:

```text
canonical product/version
marketplace
vendor product/listing IDs
plan mappings
adapter/pack version
deployment artifacts
vendor-contract observation
qualification receipts
extensions/gaps
standing
```

This record makes it possible to regenerate or replace a vendor projection without renaming the product inside the organization.

## No marketplace forks

The most expensive anti-pattern is a vendor-specific roadmap: AWS edition gains feature X, Microsoft edition gains feature Y, and direct edition has different entitlement logic. Sometimes a capability genuinely differs by market, but that difference should be represented as a projection extension or deployment capability—not as silent divergence.

If a capability is strategically product-wide, it enters the canonical graph and each market is reprojected. If a vendor-specific feature is valuable only on that market, it remains an extension linked to the canonical product.

## Customer meaning

For plans declared equivalent, normalized rights should match:

- feature access;
- quantities/limits;
- support tier;
- security promises;
- metering meaning;
- termination/data behavior.

Price can differ by route/market/offer without changing these rights if the commercial graph represents that fact.

## Regeneration

When canonical product semantics change, regenerate every affected projection and produce a capability/gap diff before publication. This is a manufacturing problem, not a series of manual tickets.

```text
G_c(v2)
  → π_AWS(v2)
  → π_MS(v2)
  → π_GCP(v2)
  → ...
  → differential qualification
```

## Standing is still local

A product can be ALIVE in AWS entitlement, PARTIAL_ALIVE in Microsoft metering, BLOCKED on SAP partner review, and UNKNOWN on a sovereign marketplace. “One product” does not create one global boolean.

## Refusals

- `REFUSED:VENDOR_SKU_AS_PRODUCT_IDENTITY`
- `REFUSED:MARKETPLACE_SPECIFIC_PRODUCT_ROADMAP_BY_DEFAULT`
- `REFUSED:VENDOR_LIMITATION_COPIED_INTO_CANONICAL_CORE`
- `REFUSED:ONE_MARKET_ALIVE_AS_GLOBAL_ALIVE`
- `REFUSED:UNEXPLAINED_RIGHTS_DIVERGENCE`

## Operational exercise

Choose AWS, Microsoft, Salesforce, and Alibaba. For the same canonical plan, map all vendor identifiers and prove what remains invariant. Then introduce one vendor-only feature and represent it without changing the canonical rights of the other projections.
