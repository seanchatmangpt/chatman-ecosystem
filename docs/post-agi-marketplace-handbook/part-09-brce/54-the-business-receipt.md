# 54. The Business Receipt

## Evidence must bind the consequence

A business receipt answers a question ordinary logs cannot reliably answer: **what exact commercial object changed, who had authority, what intent was executed, what external system observed it, what postcondition was verified, and what can now be claimed?**

```text
R = receipt(
  Identity,
  Authority,
  Intent,
  Consequence,
  Verification,
  Time,
  Evidence
)
```

## Common envelope

A receipt should contain or reference:

```text
receipt schema/version
canonical subject
marketplace + external subject IDs
capability
actor
exact authority/grant
admitted input digest
intent digest
idempotency key
pre-state
external request/result identity
post-state / verifier evidence
observed_at / effective_at
changed[]
verified[]
excluded[]
replay recipe
standing before/after
```

The goal is reconstructability, not maximal logging.

## Domain-specific receipts

### Offer receipt

Adds buyer scope, plan/version, price/term/legal digests, validity, vendor offer ID, and publication state.

### Entitlement receipt

Adds agreement ID, prior/new state, rights delta, source event, effective time, and idempotency identity.

### Fulfillment receipt

Adds target, deployment artifact digest, actuation ID, expected/observed postcondition, created resources, and compensation linkage.

### Meter receipt

Adds meter-definition version, window, source-event set digest, quantity/unit, vendor submission ID, acceptance state, and correction linkage.

### Settlement receipt

Adds vendor statement identity, matched charges/batches, fees/credits/payout, residuals, and reconciliation standing.

## Receipt is not authority

A prior receipt proves that an action happened. It does not grant permission to repeat it. Replay and follow-up operations must acquire fresh authority appropriate to their consequences.

## Independent verification

Whenever possible, the verifier should not merely echo the same untrusted output that the actuator returned. Read the vendor state, observe the runtime postcondition, or reconcile against an independent statement.

## Tamper evidence

Content addressing such as BLAKE3 can bind evidence and receipt DAGs. Cryptographic integrity does not prove semantic correctness, but it makes later mutation detectable.

## Refusals

- `REFUSED:LOG_LINE_AS_RECEIPT`
- `REFUSED:RECEIPT_WITHOUT_EXACT_SUBJECT`
- `REFUSED:MISSING_EXTERNAL_IDENTITY`
- `REFUSED:SELF_REPORTED_POSTCONDITION_ONLY`
- `REFUSED:RECEIPT_AS_REPLAY_AUTHORITY`

## Operational exercise

Define machine-readable receipts for private-offer creation, entitlement activation, Kubernetes fulfillment, meter submission, and settlement reconciliation. A reviewer who has only the receipts and referenced evidence should be able to reconstruct the commercial trace without gaining authority to repeat it.
