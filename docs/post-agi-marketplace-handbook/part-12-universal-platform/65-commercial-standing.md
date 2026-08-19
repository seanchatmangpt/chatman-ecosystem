# 65. Commercial Standing

## Standing is a typed claim over an exact subject

“Marketplace ready” is too vague to be operational. A product can have a generated listing, an approved seller account, a working entitlement adapter, an untested meter, and a blocked security review simultaneously.

Standing therefore has three coordinates:

```text
Standing(exact_subject, capability, evidence)
```

## Vocabulary

### `UNKNOWN`

The capability has not been observed or evidence is insufficient. Official documentation saying the vendor supports a capability does not prove the product implements it.

### `PARTIAL_ALIVE`

A bounded subset executed and verified. Example: customer resolution and activation executed, but lifecycle cancellation has not.

### `ALIVE`

The exact admitted subject executed against the required environment/verifier, postconditions were observed, and receipt/replay evidence verifies.

### `BLOCKED`

A known prerequisite prevents the next transition: seller approval, customer account, marketplace review, legal approval, missing credential, or external service.

### `BUILD_BROKEN`

The candidate cannot build, render, package, compile, or pass a required structural gate.

### `UNSUPPORTED`

The bounded implementation or market surface lacks the requested capability. This is topology, not a refusal.

### `REFUSED:*`

The system understood the operation and rejected it under an explicit rule.

## Per-capability standing

A marketplace row might look like:

```text
aws.seller_registration         BLOCKED
aws.saas.customer_resolution    PARTIAL_ALIVE
aws.saas.entitlement            UNKNOWN
aws.saas.metering               UNKNOWN
aws.container.package           ALIVE
aws.container.publication       BLOCKED
```

No averaging turns that into “80% marketplace ready.” The matrix preserves actionable edges.

## Evidence ladder

```text
inspection
→ structural validation
→ deterministic generation
→ local behavioral tests
→ gym/contract qualification
→ vendor sandbox execution
→ live exact-subject execution
→ receipt/replay
```

Each rung is useful. Only the rung required by the claim can crown it.

## Invalidation

Standing must be reconsidered when relevant identity changes: source commit, product version, pack, adapter, artifact digest, marketplace API/contract, seller account, environment, authority policy, or verifier.

A cache can accelerate requalification only when those identities match or equivalence is proven.

## Refusals

- `REFUSED:LISTING_PRESENT_AS_ALIVE`
- `REFUSED:UNSUPPORTED_USED_AS_REFUSAL`
- `REFUSED:BLOCKED_USED_TO_HIDE_BUILD_DEFECT`
- `REFUSED:WORKFLOW_METADATA_AS_RUN_EVIDENCE`
- `REFUSED:CAPABILITY_STANDING_TRANSFERRED_TO_WHOLE_MARKET`

## Operational exercise

Take ten marketplace capabilities from the current platform. Assign exact subjects and standing using only observed evidence. If no execution evidence exists, use UNKNOWN even if the code looks complete. Record the next cheapest falsifier for every non-ALIVE row.
