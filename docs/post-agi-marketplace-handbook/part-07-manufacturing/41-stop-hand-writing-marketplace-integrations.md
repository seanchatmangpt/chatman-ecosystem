# 41. Stop Hand-Writing Marketplace Integrations

## Duplication is the integration tax we can remove

A conventional multi-market strategy creates one team or adapter per vendor. Each implementation repeats product mapping, customer resolution, entitlement transitions, meter code, error handling, listing metadata, tests, and documentation. Even when every individual integration is well written, the portfolio drifts because semantics are copied rather than projected.

The repeated work should be lifted into canonical executable knowledge.

```text
Bespoke integrations
  → identify repeated semantics
  → canonical ontology + constraints
  → vendor projection rules
  → generated artifacts
  → independent qualification
```

## Do not abstract before equivalence

The cure for duplication is not a premature `IMarketplaceSubscription` abstraction. Shared structure is admitted only after semantics are compared.

AWS agreements, Microsoft subscriptions, Google entitlements, Salesforce package licenses, Alibaba service instances, and Snowflake listing access can participate in a shared commercial graph without being the same object.

The canonical layer owns concepts such as organization, agreement, entitlement, meter, fulfillment, and receipt. Vendor packs own the mappings.

## The generated surface

Good generation targets include:

- vendor wire schemas and typed models;
- product/plan/listing metadata;
- identifier mapping tables;
- webhook parsers and intent constructors;
- meter submission clients;
- deployment/package manifests;
- negative/positive fixtures;
- documentation projections;
- capability descriptors;
- receipt schemas.

The shared state machine, authority policy, and canonical ontology remain the source. Generated files are replaceable outputs.

## Drift becomes a build failure

If listing metadata, adapter code, and documentation all derive from one graph, changing a canonical plan can regenerate every projection. A stale vendor projection becomes detectable because its source digest no longer matches.

```text
canonical digest
  → generation receipt
  → projection digest
  → qualification receipt
```

Manual console changes should either be imported back as observed vendor state and reconciled, or refused by policy for fields that must be generated.

## Speed without false standing

Generation can compress interface authorship from days to seconds. It does not compress marketplace seller review, security certification, buyer procurement, or live execution. Those remain external or runtime admissions.

The gain is still enormous: engineering time moves from retyping vendor contracts to ontology, constraints, differential tests, and high-value exceptions.

## Refusals

- `REFUSED:COPY_PASTE_AS_PORTABILITY`
- `REFUSED:ABSTRACTION_BEFORE_EQUIVALENCE`
- `REFUSED:GENERATED_FILE_HAND_EDIT`
- `REFUSED:STALE_PROJECTION_DIGEST`
- `REFUSED:GENERATION_SUCCESS_AS_ALIVE`

## Operational exercise

Compare two existing marketplace adapter designs. Extract the shared commercial semantics into canonical objects and leave every non-equivalent vendor behavior in a pack-specific extension. The result should generate both candidates without moving any DO authority into the generator.
