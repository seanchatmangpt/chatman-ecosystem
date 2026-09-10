# Status Is a Type

> **Subject identity:** `dyson:status-is-a-type:64403d44b633`
> **Domain:** `verification`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Status Is a Type** exists because it changes a concrete decision inside **Part XX — Verification at Civilization Scale**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Status Is a Type**, the primary state variables include **subject**, **execution**, and **postcondition**; the control or consequence variables include **verifier**, **receipt**, and **replay**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Status Is a Type** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [UNKNOWN](73-01-unknown.md)
- [PARTIAL_ALIVE](73-02-partial-alive.md)
- [ALIVE](73-03-alive.md)
- [BLOCKED](73-04-blocked.md)
- [BUILD_BROKEN](73-05-build-broken.md)
- [UNSUPPORTED](73-06-unsupported.md)
- [REFUSED](73-07-refused.md) For **Status Is a Type**, this reusable domain rule is evaluated against `dyson:status-is-a-type:64403d44b633`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Status Is a Type**, standing belongs to an exact subject and revision. The evidence chain is

```text
observed -> admitted -> executed -> changed -> verified -> receipted -> replayable
```

Those predicates are not interchangeable. `dyson:status-is-a-type:64403d44b633` reaches `ALIVE` only when the owning verifier observes the required postcondition against the admitted subject and replay reconstructs why the claim was made. A different SHA, environment, world model, or verifier is a different subject.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:status-is-a-type:64403d44b633` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | subject, execution, postcondition with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | verifier, receipt or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Status Is a Type**, Change only the subject SHA and rerun receipt lookup. An exact-subject verifier refuses standing inheritance even when the candidate appears behaviorally similar.

## Questions the design must answer

1. For **Status Is a Type**: What exact subject executed and what changed?
2. For **Status Is a Type**: Which evidence would downgrade standing?
3. For **Status Is a Type**: Can replay reconstruct the decision without repeating consequence?

## Executable representation

```yaml
subject: dyson:status-is-a-type:64403d44b633
topic: "Status Is a Type"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- A green workflow on another SHA is presented as exact-subject standing.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Status Is a Type**.
- **Hidden assumption:** subject or execution is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Status Is a Type**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:status-is-a-type:64403d44b633`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Status Is a Type** subject/revision is named.
- [ ] Required subject, execution, and postcondition observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Status Is a Type** is admitted, downstream systems may consume its subject, execution, and postcondition claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Status Is a Type** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
