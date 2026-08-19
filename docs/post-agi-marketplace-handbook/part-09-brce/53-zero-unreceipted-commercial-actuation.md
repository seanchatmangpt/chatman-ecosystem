# 53. Zero Unreceipted Commercial Actuation

## Commercial side effects are consequential

Marketplace engineering can create offers, agreements, customer rights, infrastructure, meter submissions, charges, credits, refunds, publication state, and termination. These are not ordinary helper-function side effects.

BRCE is the exclusive DO path:

```text
SELECT → CONSTRUCT → ADMIT AUTHORITY → DO → VERIFY → RECEIPT
```

Zero consequential commercial actuation occurs outside this envelope.

## SELECT

SELECT chooses among admitted candidates: which marketplace, plan, private-offer configuration, deployment target, repair, or route. Selection can be optimized, simulated, or agent-assisted without mutating the outside world.

## CONSTRUCT

CONSTRUCT produces an immutable intent containing:

```text
exact subject
desired transition
preconditions
vendor projection
idempotency identity
expected postcondition
cost/risk bounds
required authority
```

Generated code, model output, workflow input, and webhook events can all contribute to construction. None are authority.

## DO

The broker checks exact authority immediately before actuation. The grant must cover actor, capability, subject, environment, marketplace/account, consequence class, limits, and validity.

Valid credentials prove that a technical channel might accept a call. They do not prove the caller is authorized by the product governance model to make it.

## Verify after actuation

Do not treat the actuator response as the receipt. Observe the target state independently where possible:

- offer exists with expected buyer/terms;
- entitlement reached expected state;
- deployment is customer-ready;
- meter batch is accepted once;
- refund/credit appears correctly;
- listing version is actually published.

## Receipt

The receipt binds identity, authority, intent, external IDs, consequence, verification, time, evidence digests, exclusions, and standing delta.

Replay consumes the receipt without repeating DO.

## Hooks manufacture intents

A webhook, CI hook, GitHub event, queue consumer, or LLM agent can trigger construction. It must never become a hidden direct actuator merely because event-driven architecture makes that convenient.

## Refusals

- `REFUSED:DIRECT_MARKETPLACE_DO`
- `REFUSED:CREDENTIAL_AS_AUTHORITY`
- `REFUSED:HOOK_AS_ACTUATOR`
- `REFUSED:MISSING_IDEMPOTENCY_FOR_FINANCIAL_DO`
- `REFUSED:ACTUATOR_RESPONSE_AS_VERIFICATION`
- `REFUSED:REPLAY_REACTUATES`

## Operational exercise

Write BRCE envelopes for a meter submission, a private-offer publication, an entitlement suspension, and a refund. Identify the shared constitutional fields and the capability-specific authority. Prove replay cannot send the same consequence again.
