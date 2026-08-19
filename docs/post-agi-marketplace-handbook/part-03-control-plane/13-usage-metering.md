# 13. Usage Metering

## A meter is a measurement system

Calling a marketplace metering API is the last step of metering, not the first. A defensible meter begins with a declared economic quantity, observation boundary, unit, precision, time window, deduplication rule, aggregation function, late-data policy, and correction mechanism.

```text
UsageBatch = aggregate(normalize(ObservedUsageEvents), AdmittedWindow)
```

The marketplace submission is a projection of that batch. The API response can confirm whether the vendor accepted the report; it cannot manufacture the underlying usage.

## Choose a quantity a customer can reason about

Possible units include seats, requests, compute time, storage, tokens, transactions, protected assets, processed documents, or outcomes. The correct unit depends on the product contract and value model. A unit chosen because it is easy to count can create a technically correct but commercially indefensible bill.

Every `UsageDimension` should include:

```text
id
unit
measurement_source
precision
aggregation
window_policy
late_data_policy
correction_policy
pricing_bindings
version
```

## Raw events and billable batches are different

Raw events can arrive more than once, late, or with corrections. They should have durable event identity and provenance. A batch freezes an admitted set of events for a particular agreement/window.

```text
OPEN → FROZEN → SUBMITTING → ACCEPTED
                    ↘ REJECTED → CORRECTING → FROZEN
```

Freezing matters because reconciliation later must prove which measured facts produced the quantity sent to the marketplace.

## Time is contractual

“Monthly usage” is incomplete without timezone, boundary convention, effective plan, and rule for usage spanning a plan change. The meter must be able to answer which contract and price were effective for each quantity.

Late data should not silently mutate a settled period. Depending on vendor capabilities, it may produce an adjustment, a new correction batch, or a typed exception requiring finance review.

## Idempotency

Submission retries must distinguish “vendor definitely rejected” from “response lost after possible acceptance.” If the marketplace offers an idempotency or unique usage key, use it. If not, observe vendor state before repeating a financial DO whenever possible.

## Metering is not pricing

The same usage quantity can be priced differently by plan, term, private offer, credit, or committed spend. Keep measurement invariant and apply commercial policy separately.

## Refusals

- `REFUSED:IMPLEMENTATION_DETAIL_AS_METER`
- `REFUSED:USAGE_WITHOUT_UNIT`
- `REFUSED:DUPLICATE_USAGE_EVENT`
- `REFUSED:UNVERSIONED_METER_SEMANTICS`
- `REFUSED:AMBIGUOUS_FINANCIAL_RETRY`
- `REFUSED:ESTIMATE_AS_MEASUREMENT`

## Operational exercise

Choose one usage dimension for the platform. Specify its unit, authoritative observation source, event identity, precision, window, plan-change behavior, late-data policy, correction path, marketplace mappings, and receipt. Then reconstruct one submitted batch from raw events without consulting the billing dashboard.
