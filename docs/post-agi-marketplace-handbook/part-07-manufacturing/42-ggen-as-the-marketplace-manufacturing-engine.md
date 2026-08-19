# 42. ggen as the Marketplace Manufacturing Engine

## Ontology to artifact

`ggen` is the deterministic manufacturer in the marketplace architecture. It consumes admitted semantic input and renders concrete projections: schemas, adapters, listing metadata, deployment packages, fixtures, documentation, and qualification configuration.

```text
O* → graph/query/template → ggen → artifact
```

The crucial word is **manufacturer**, not authority. A generated AWS metering request can be structurally perfect and still have no permission to send itself.

## Source capsule

Every marketplace generation run should pin:

```text
canonical ontology digest
product graph digest
marketplace pack version
vendor-contract observation/version
ggen version
query/template digests
generation configuration
```

That source capsule makes generation replayable and prevents “same template name” from being mistaken for the same manufacturer.

## Query before template

The graph owns meaning. Queries select admitted facts needed for an artifact. Templates render them. This keeps presentation from becoming business logic.

Example:

```text
Canonical Plan
  → query: marketplace plan projection
  → template: vendor listing schema
  → generated listing candidate
```

A template must not invent price, support, entitlement, or security claims absent from the graph.

## Multiple projections from one node

One canonical plan can generate:

- AWS offer/product metadata;
- Microsoft plan metadata;
- Google product metadata;
- Oracle SKU/meter mappings;
- Alibaba SKU projection;
- documentation tables;
- entitlement mapping code;
- meter fixtures.

That correspondence is more valuable than generating one file quickly. It removes manual synchronization between code, docs, and commerce.

## Manufacture receipt

A generation receipt records source identities, output paths/digests, deterministic replay command, exclusions, and whether generated output still needs compilation, semantic admission, runtime qualification, or vendor approval.

```text
A = μ_ggen(O*)
```

`A` is a candidate artifact with manufacture evidence. `Standing(A)` is determined by downstream verification.

## Failure transparency

If the vendor pack lacks a mapping for a canonical feature, generation should produce a typed failure or gap manifest rather than a plausible empty field.

Useful failures include:

- `REFUSED:QUERY_RESULT_INCOMPLETE`
- `REFUSED:UNSUPPORTED_PLAN_PROJECTION`
- `REFUSED:TEMPLATE_INVENTS_UNADMITTED_FACT`
- `REFUSED:SOURCE_DIGEST_DRIFT`
- `REFUSED:NONDETERMINISTIC_OUTPUT`

## Operational exercise

Define one `ggen` project that reads a canonical plan and emits an entitlement adapter mapping, listing metadata, meter dimension schema, contract-test fixture, and documentation row. All outputs must bind the same canonical plan ID and source digest.
