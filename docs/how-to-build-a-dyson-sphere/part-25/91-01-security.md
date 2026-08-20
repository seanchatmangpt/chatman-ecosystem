# Security

**Parent:** [CASTLE](91-castle.md)

> **Subject identity:** `dyson:security:ed639c0e3e30`
> **Domain:** `security`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Security** exists because it changes a concrete decision inside **CASTLE**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Security**, the primary state variables include **principal**, **credential**, and **attestation**; the control or consequence variables include **scope**, **revocation**, and **tamper evidence**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Security** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Security** is modeled as bounded reachability. A consequential grant binds

```text
(actor, exact_subject, intent_digest, capability, scope,
 not_before, expires_at, policy_version, required_postcondition)
```

Possession of a credential or network path is never enough. `dyson:security:ed639c0e3e30` also needs revocation state, content/software identity where relevant, and evidence that expired, premature, wrong-subject, wrong-intent, and over-scoped grants fail closed. `SELECT`, `CONSTRUCT`, and `DO` remain distinct authority classes.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:security:ed639c0e3e30` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | principal, credential, attestation with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | scope, revocation or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Security**, Test valid, expired, wrong-subject, and replayed requests. The authorization system is meaningful only if the negative cases fail closed.

## Questions the design must answer

1. For **Security**: Which principal can reach this capability under what scope?
2. For **Security**: What compromised component is assumed?
3. For **Security**: How are expiry and revocation made unreachable rather than advisory?

## Executable representation

```json
{
  "subject": "dyson:security:ed639c0e3e30",
  "intent": "Security",
  "actor": "explicit",
  "authority_scope": "explicit",
  "validity_window": "required for DO",
  "revocation": "checked",
  "appeal_or_refusal_path": "explicit",
  "postcondition": "named before execution"
}
```

## Failure modes and counterexamples

- Credential possession is treated as authority after scope expiry, revocation, or subject drift.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Security**.
- **Hidden assumption:** principal or credential is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Security**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:security:ed639c0e3e30`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Security** subject/revision is named.
- [ ] Required principal, credential, and attestation observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Security** is admitted, downstream systems may consume its principal, credential, and attestation claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Security** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
