# 11. Entitlements

## Entitlement is commercial authority represented as state

Entitlement answers: **what is this customer currently allowed to receive because of an admitted agreement?** It is not a payment event, feature flag, deployment record, or login session.

That makes entitlement the boundary between commercial truth and operational behavior.

```text
Agreement → Entitlement → Runtime authorization / Fulfillment
```

A marketplace adapter may translate vendor lifecycle events, but every source should converge on one canonical entitlement state machine.

## State machine

A useful baseline is:

```text
PENDING → ACTIVE
ACTIVE → CHANGING → ACTIVE
ACTIVE → SUSPENDED → ACTIVE
ACTIVE → EXPIRING → EXPIRED
ACTIVE|SUSPENDED|EXPIRED → REVOKED
```

The exact states may differ by product, but the invariants should not:

- every entitlement derives from an admitted agreement or equivalent commercial grant;
- quantity and feature rights are explicit;
- effective time is preserved;
- retries are idempotent;
- delayed older events cannot silently resurrect newer terminal state;
- revocation history is retained;
- runtime systems consume canonical entitlement, not raw vendor payloads.

## Source adapters are thin

AWS, Microsoft, Google, Oracle, Stripe/direct billing, Salesforce licensing, and other sources can provide different event schemas. They should normalize into a canonical `EntitlementEvent` rather than implement parallel transition logic.

```text
VendorEvent
  → verify/admit
  → normalize
  → applyEntitlementEvent(source, event)
  → entitlement transition
  → receipt
```

This architecture is already aligned with the Chatman ecosystem's current direction: the base branch records a generic `applyEntitlementEvent(source, event)` path so external commerce sources can become adapters rather than independent state machines.

## Idempotency and ordering

Event identity must survive retries. If a vendor supplies a stable event or subscription version, preserve it. Otherwise construct an idempotency identity from admitted immutable fields.

Ordering uses effective semantics, not network arrival. A `cancel effective Friday` event observed before an older `plan changed Wednesday` retry must not be undone simply because the retry arrived later.

## Suspension policy

Suspension is not always immediate deletion. A commercial right can be suspended while data retention, export, legal hold, or recovery obligations remain. Runtime authorization, background processing, customer access, and data deletion therefore need separate policy.

## Refusals

- `REFUSED:PARALLEL_MARKETPLACE_STATE_MACHINE`
- `REFUSED:WEBHOOK_AS_FEATURE_FLAG`
- `REFUSED:STALE_EVENT_REACTIVATION`
- `REFUSED:DUPLICATE_ENTITLEMENT_TRANSITION`
- `REFUSED:RIGHT_WITHOUT_AGREEMENT`

## Operational exercise

Implement or specify property tests for create, activate, plan change, suspend, reinstate, cancel, expire, and revoke. Then permute event arrival order and inject duplicates. Equivalent effective event sets should converge on equivalent canonical entitlement state or produce a typed ambiguity rather than silently diverge.
