# Appendix D — Commercial State Machines

Commercial state must be explicit because marketplaces deliver asynchronous, repeated, delayed, and sometimes contradictory observations.

## Agreement

```text
DRAFT → OFFERED → ACCEPTED → ACTIVE
ACTIVE → AMENDED → ACTIVE
ACTIVE → RENEWED → ACTIVE
ACTIVE → TERMINATING → TERMINATED
```

An offer is not an agreement. An accepted agreement is immutable history; later commercial changes are transitions or successor versions.

## Entitlement

```text
PENDING → ACTIVE
ACTIVE → SUSPENDED → ACTIVE
ACTIVE → CHANGING → ACTIVE
ACTIVE → EXPIRING → EXPIRED
ACTIVE|SUSPENDED|EXPIRED → REVOKED
```

A stale event cannot move a terminal or later-effective state backward without an explicit vendor semantic that permits it.

## Fulfillment

```text
REQUESTED → PLANNED → ACTUATING → VERIFYING → READY
                         ↘ FAILED → RETRYING
                         ↘ COMPENSATING → COMPENSATED
READY → DEPROVISIONING → DEPROVISIONED
```

Entitlement and fulfillment are intentionally separate. A customer can hold an active right while deployment is delayed. That condition needs support and SLO semantics rather than state collapse.

## Meter batch

```text
OPEN → FROZEN → SUBMITTING → ACCEPTED
                    ↘ REJECTED → CORRECTING → FROZEN
```

A frozen batch is content-addressed. Corrections create a new batch or explicit adjustment according to vendor rules.

## Settlement reconciliation

```text
UNMATCHED → PARTIALLY_MATCHED → MATCHED
UNMATCHED|PARTIALLY_MATCHED → EXCEPTION → RESOLVED
```

Never manufacture a match by dropping unexplained residuals.

## Effective-time law

Every transition capable of arriving asynchronously should retain:

```text
observed_at
effective_at
source_sequence_or_version_if_available
idempotency_key
source_event_id
```

Ordering by arrival time alone is not admitted unless the vendor contract guarantees it.
