# 55. Replay

## Replay reconstructs; it does not repeat commerce

A commercial system needs to answer historical questions without re-running side effects: What rights did the customer have at noon? Which usage events produced the submitted quantity? Which private offer created the agreement? Why was access suspended? Which charge became this payout?

Replay consumes immutable evidence and recomputes state.

```text
Replay(ReceiptDAG, ExactSourceIdentities) → ReconstructedState
side_effects = ∅
```

## Inputs

A replay capsule binds:

```text
canonical ontology/version
product/plan versions
pricing versions
marketplace adapter/pack version
receipt DAG
source event digests
effective-time rules
replay tool/version
```

Using today's price table to reconstruct last year's contract is not replay. It is reinterpretation.

## State reconstruction

Replay orders events according to admitted commercial semantics, preserving observed time separately from effective time. It applies the same canonical transition functions used by runtime code without calling vendor write APIs.

Expected outputs include:

- agreement state at a cutoff;
- entitlement state and rights;
- fulfillment trace;
- measured/billable usage;
- meter-batch composition;
- reconciliation joins;
- standing/exclusions at the historical subject.

## External observations

Some facts originate outside the repository: marketplace agreement IDs, vendor acceptance, settlement records, partner approvals. Replay verifies the preserved observation/receipt of those facts; it does not regenerate the external event.

Where an external fact is missing, reconstruction returns `UNKNOWN` rather than manufacturing an answer.

## Replay mismatch

A mismatch can indicate receipt corruption, changed transition semantics, missing source identity, nondeterminism, or a genuine historical inconsistency. Preserve the mismatch as evidence and localize the failed transition.

```text
REPLAY_MATCH
REPLAY_MISMATCH:STATE
REPLAY_MISMATCH:DIGEST
REPLAY_BLOCKED:MISSING_EVIDENCE
```

## No actuation authority

Replay tools should be physically incapable of calling offer, meter, refund, entitlement, or deployment mutation APIs. This is stronger than a runtime flag. It ensures audit/reconstruction cannot accidentally create a second charge.

## Refusals

- `REFUSED:REPLAY_SENDS_MARKETPLACE_WRITE`
- `REFUSED:LATEST_PRICE_FOR_HISTORICAL_AGREEMENT`
- `REFUSED:MISSING_RECEIPT_SILENTLY_SKIPPED`
- `REFUSED:MUTABLE_DASHBOARD_AS_REPLAY_SOURCE`
- `REFUSED:RECONSTRUCTION_MISMATCH_HIDDEN`

## Operational exercise

Reconstruct a customer's entitlement and billable usage at a historical cutoff using only versioned source plus receipts. Then prove at the capability/permission layer that the replay executable cannot invoke a marketplace write operation.
