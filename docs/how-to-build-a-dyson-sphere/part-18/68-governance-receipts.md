# Governance Receipts

> **Subject identity:** `dyson:governance-receipts:48a9ec8543a6`
> **Domain:** `governance`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Governance Receipts** exists because it changes a concrete decision inside **Part XVIII — Governance**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Governance Receipts**, the primary state variables include **jurisdiction**, **right**, and **duty**; the control or consequence variables include **delegation**, **appeal**, and **amendment**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Governance Receipts** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Identity](68-01-identity.md)
- [Authority](68-02-authority.md)
- [Decision](68-03-decision.md)
- [Consequence](68-04-consequence.md)
- [Replay](68-05-replay.md)
- [Standing](68-06-standing.md) For **Governance Receipts**, this reusable domain rule is evaluated against `dyson:governance-receipts:48a9ec8543a6`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Governance Receipts**, governance is an executable decision protocol. `dyson:governance-receipts:48a9ec8543a6` binds jurisdiction, rule version, authorized decision-maker, affected subjects, evidence/reasons, effective interval, appeal path, and amendment provenance. Appeals are typed transitions that may stay, affirm, narrow, or reverse a decision while preserving the original causal record; they are not an informal comment channel.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:governance-receipts:48a9ec8543a6` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | jurisdiction, right, duty with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | delegation, appeal or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Governance Receipts**, Replay a historical decision under a later rule version. Historical legality uses the then-effective rule; a new action uses the current rule. Immutable policy-version references make both evaluations possible.

## Questions the design must answer

1. For **Governance Receipts**: Which jurisdiction and rule authorize the decision?
2. For **Governance Receipts**: Who can challenge it and through which typed transition?
3. For **Governance Receipts**: How are conflicting jurisdictions reconciled under delay?

## Executable representation

```json
{
  "subject": "dyson:governance-receipts:48a9ec8543a6",
  "intent": "Governance Receipts",
  "actor": "explicit",
  "authority_scope": "explicit",
  "validity_window": "required for DO",
  "revocation": "checked",
  "appeal_or_refusal_path": "explicit",
  "postcondition": "named before execution"
}
```

## Failure modes and counterexamples

- A policy engine invents authority from ambiguous prose or applies a current rule retroactively.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Governance Receipts**.
- **Hidden assumption:** jurisdiction or right is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Governance Receipts**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:governance-receipts:48a9ec8543a6`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Governance Receipts** subject/revision is named.
- [ ] Required jurisdiction, right, and duty observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Governance Receipts** is admitted, downstream systems may consume its jurisdiction, right, and duty claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Governance Receipts** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
