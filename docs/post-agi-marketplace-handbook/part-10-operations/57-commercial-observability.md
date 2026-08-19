# 57. Commercial Observability

## Trace the business graph without leaking it

Commercial observability joins technical telemetry to product, agreement, entitlement, tenant, marketplace, usage, offer, and settlement identities. The objective is to answer customer and operator questions end to end without turning logs into a repository of secrets or financial PII.

```text
TechnicalContext ⊗ CommercialContext → Traceable lifecycle
```

## Correlation identities

A lifecycle trace can propagate opaque canonical IDs such as:

```text
product_version_id
organization_id
agreement_id
entitlement_id
fulfillment_id
usage_batch_id
marketplace_projection_id
receipt_id
```

Vendor IDs can be attached in protected structured fields. Access tokens, purchase tokens, secrets, raw legal documents, and unnecessary personal data should not be logged.

## Purchase-to-first-value trace

A useful trace spans:

```text
purchase observation
→ customer resolution
→ entitlement transition
→ fulfillment job
→ runtime readiness
→ first usage
→ first meter batch
→ vendor acceptance
```

Each span carries exact canonical identity and receipt linkage. A support engineer can then answer “why can this customer not use the product?” without querying six dashboards by email address.

## Role-specific views

Engineering needs transition latency and errors. Finance needs meter/settlement/reconciliation lineage. Support needs customer-facing entitlement and fulfillment state. Security needs privileged actuation and identity. Sales operations needs offer/agreement state.

Use one evidence graph with access-controlled projections rather than duplicating truth into team spreadsheets.

## Cardinality and privacy

Commercial identifiers can create high-cardinality metrics. Prefer traces/log events or bounded label sets where appropriate. Do not put customer names, email addresses, contract text, or raw marketplace tokens into metric labels.

## Explainability

Every customer-affecting state should expose reason and source:

```text
ENTITLEMENT=SUSPENDED
source=marketplace_event
source_event_id=...
effective_at=...
agreement=...
receipt=...
```

“Feature flag off” is not enough.

## Cross-market normalization

Normalize metrics such as entitlement latency and meter rejection so operations can compare marketplaces, while retaining vendor-specific diagnostic dimensions. This is another projection problem: shared semantics plus extensions.

## Refusals

- `REFUSED:RAW_PURCHASE_TOKEN_IN_LOG`
- `REFUSED:PII_AS_METRIC_LABEL`
- `REFUSED:VENDOR_ID_WITHOUT_CANONICAL_MAPPING`
- `REFUSED:DASHBOARD_WITHOUT_RECEIPT_LINEAGE`
- `REFUSED:FEATURE_FLAG_AS_COMMERCIAL_EXPLANATION`

## Operational exercise

Design an OpenTelemetry-style trace for purchase through first metered usage. Mark which fields are canonical correlation IDs, which vendor IDs need protected access, which values are forbidden in telemetry, and how the trace links to receipts and reconciliation.
