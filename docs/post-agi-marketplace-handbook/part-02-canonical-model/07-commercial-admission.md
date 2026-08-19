# 7. Commercial Admission

## Observed is not admitted

A marketplace webhook can be authentic and still be stale, mapped to the wrong product version, or irrelevant to the current agreement. A signed offer can be genuine and still be expired. A vendor document can be official and still describe the wrong product type or API generation.

Commercial admission is the transformation from candidate observation `O` to bounded observation `O*` that may participate in manufacture.

```text
O* = admit(O, identity, authority, constraints, freshness, subject)
```

Admission is deliberately separate from DO. It proves that facts may be used to construct an intent; it does not grant permission to change customer rights or external systems.

## The admission envelope

For an inbound commercial event, evaluate:

1. **Issuer identity** — which marketplace, account, tenant, certificate, token issuer, or authenticated channel produced it?
2. **Subject identity** — which canonical product, offer, agreement, organization, or entitlement does it concern?
3. **Schema and protocol** — is this payload admitted by the versioned vendor contract?
4. **Freshness** — when was it observed and when is it effective?
5. **Mapping** — do vendor product/plan identifiers resolve to exact canonical objects?
6. **State preconditions** — is the requested transition legal from current state?
7. **Authority ceiling** — what consequence, if any, may later be brokered?
8. **Idempotency** — has the same commercial fact already been applied?

Only then is a canonical event manufactured.

## Admission for documentation

Official documentation is also `O`. It enters `O*` only after applicability is bounded by marketplace program, product type, region, seller type, API generation, and observation date. This prevents a familiar failure mode: reading a correct page about a different offer class and implementing it as universal truth.

Conflicting official observations are preserved until resolved. The system does not average them into a convenient contract.

## Status is typed

`UNKNOWN` means evidence is insufficient. `UNSUPPORTED` means the bounded market or implementation lacks a capability. `REFUSED:*` means a known rule rejects the requested transition. `BLOCKED` means a known prerequisite prevents progress. These states have different remediation paths.

Examples:

- `REFUSED:INVALID_SIGNATURE`
- `REFUSED:ISSUER_MISMATCH`
- `REFUSED:SUBJECT_UNRESOLVED`
- `REFUSED:STALE_EVENT`
- `REFUSED:PLAN_MAPPING_MISSING`
- `REFUSED:ILLEGAL_STATE_TRANSITION`
- `REFUSED:AUTHORITY_MISSING`
- `UNKNOWN:VENDOR_SEMANTICS_UNRESOLVED`

## No manufactured missing facts

If a marketplace event omits a field needed to identify the agreement, the model must find a lawful external observation path or stop. It cannot infer the missing agreement from the most recent customer event merely because that guess is usually right.

The same rule applies to legal and financial facts. A generated EULA draft is not an approved EULA. A seller registration form is not seller approval. A calculated invoice is not marketplace settlement.

## Falsifier

Admission is defective if a malformed, stale, incorrectly mapped, or unauthorized observation can reach the same `O*` state as its valid counterpart.

## Operational exercise

Define admission for two events: `subscription-created` and `meter-submit`. Include exact subject resolution, effective-time handling, idempotency, authority ceiling, at least five typed refusals, and one explicit `UNKNOWN` branch. Then prove that neither admission function can itself perform external DO.
