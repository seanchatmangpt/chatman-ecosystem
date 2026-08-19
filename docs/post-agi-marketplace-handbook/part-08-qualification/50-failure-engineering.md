# 50. Failure Engineering

## Failure maps topology

A failed marketplace edge should tell us which transition, dependency, or authority boundary is broken. It should not collapse into “marketplace integration failed.”

```text
Failure ≠ GraphFailure
Failure = TypedEdgeCondition
```

This framing preserves the rest of the product graph and makes repair local.

## Failure classes

### Observation failures

Invalid signature, unknown issuer, schema drift, missing field, stale event, duplicate event, or unresolved customer/product mapping.

### Construction failures

Ontology violation, unsupported projection, template error, invalid package, price model mismatch, or deterministic-generation drift.

### Authority failures

Missing grant, expired token, wrong marketplace account, buyer mismatch, action exceeds delegated scope, or legal/business approval absent.

### Actuation failures

Vendor unavailable, rate limited, request rejected, partial provisioning, timeout with ambiguous external consequence, or marketplace state conflict.

### Verification failures

The API says success but entitlement, deployment, meter, listing, or settlement postcondition is absent or wrong.

### Reconciliation failures

Missing settlement line, quantity mismatch, duplicate charge, wrong fee, currency mismatch, or unmatched refund/credit.

## Repair protocol

1. Preserve the failing observation and exact subject.
2. Classify the failed transition.
3. Decide whether the prior DO definitely happened, definitely did not happen, or is ambiguous.
4. Construct the narrowest reversible repair.
5. Admit authority only for the necessary consequence.
6. Execute once.
7. Verify the boundary postcondition.
8. Encode a permanent negative fixture/property.
9. Expand validation only after the local edge passes.

Never rerun an unchanged failure without a new hypothesis.

## Ambiguous financial failure

The hardest class is a timeout after sending a potentially billable operation. A generic retry policy is unsafe. Observe vendor state, use an idempotency identity if supported, or escalate to manual/finance authority if external state cannot be determined.

`UNKNOWN` is cheaper than duplicate money movement.

## Compensation

Compensation is a new DO. A failed deployment does not authorize deleting arbitrary resources. A mistaken meter batch does not authorize issuing an unbounded refund. Every compensating intent has exact subject and authority.

## Permanent guards

Every production or qualification defect should leave a guard: refusal, fixture, schema constraint, property test, theorem, runbook, or monitoring rule. Otherwise the organization pays to learn the same failure twice.

## Operational exercise

Build a failure matrix across entitlement, fulfillment, metering, offer publication, and settlement. Classify each failure as retry-safe, observe-before-retry, compensate, manual-authority, refused, blocked, unsupported, or unknown. Add one regression fixture for every nontrivial edge.
