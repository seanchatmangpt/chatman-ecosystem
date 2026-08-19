# Appendix F — Qualification Ladder

Qualification advances evidence without collapsing types.

## UNKNOWN

The capability has not been sufficiently observed. Documentation may suggest support, but product standing is absent.

## PARTIAL_ALIVE

A bounded subset executed and passed its required verifier. The boundary must be explicit—for example, entitlement activation may be PARTIAL_ALIVE while metering remains UNKNOWN.

## ALIVE

The exact admitted subject executed against the exact required environment and verifier. Postconditions were independently observed, receipts verify, and replay/reconstruction matches.

## BLOCKED

The next transition is known but cannot currently execute because an external prerequisite or authority is missing. Examples include seller enrollment, marketplace review, missing test account, or customer legal approval.

## BUILD_BROKEN

The candidate fails construction, compilation, packaging, schema validation, or a required pre-execution gate.

## UNSUPPORTED

The bounded implementation or vendor surface does not implement the requested capability. This is not a refusal; it is topology.

## REFUSED

The system understood the request and rejected it by rule.

```text
REFUSED:AUTHORITY_MISSING
REFUSED:STALE_EVENT
REFUSED:INVALID_SIGNATURE
REFUSED:PLAN_MAPPING_MISSING
REFUSED:UNRECEIPTED_ACTUATION
REFUSED:DOUBLE_BILLING_RISK
REFUSED:PROJECTION_INVARIANT_VIOLATION
```

## Promotion law

```text
UNKNOWN
  → structural candidate
  → simulated/contract-qualified
  → PARTIAL_ALIVE
  → live exact-subject execution
  → ALIVE
```

There is no lawful arrow from documentation presence, source inspection, successful generation, or workflow existence directly to ALIVE.

## Invalidation

Standing must be reconsidered when product version, adapter, marketplace contract, pricing semantics, runtime, authority policy, verifier, or relevant environment identity changes.
