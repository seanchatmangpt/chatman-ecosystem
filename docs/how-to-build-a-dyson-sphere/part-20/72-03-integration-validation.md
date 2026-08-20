# Integration Validation

**Parent:** [The Validation Ladder](72-the-validation-ladder.md)

> **Subject identity:** `dyson:integration-validation:3b041508dc2a`
> **Domain:** `verification`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Integration Validation** exists because it changes a concrete decision inside **The Validation Ladder**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Integration Validation**, the primary state variables include **subject**, **execution**, and **postcondition**; the control or consequence variables include **verifier**, **receipt**, and **replay**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Integration Validation** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Integration Validation**, standing belongs to an exact subject and revision. The evidence chain is

```text
observed -> admitted -> executed -> changed -> verified -> receipted -> replayable
```

Those predicates are not interchangeable. `dyson:integration-validation:3b041508dc2a` reaches `ALIVE` only when the owning verifier observes the required postcondition against the admitted subject and replay reconstructs why the claim was made. A different SHA, environment, world model, or verifier is a different subject.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:integration-validation:3b041508dc2a` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | subject, execution, postcondition with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | verifier, receipt or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Integration Validation**, Change only the subject SHA and rerun receipt lookup. An exact-subject verifier refuses standing inheritance even when the candidate appears behaviorally similar.

## Questions the design must answer

1. For **Integration Validation**: What exact subject executed and what changed?
2. For **Integration Validation**: Which evidence would downgrade standing?
3. For **Integration Validation**: Can replay reconstruct the decision without repeating consequence?

## Executable representation

```yaml
subject: dyson:integration-validation:3b041508dc2a
topic: "Integration Validation"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Integration Validation**.
- **Hidden assumption:** subject or execution is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Integration Validation**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:integration-validation:3b041508dc2a`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Integration Validation** subject/revision is named.
- [ ] Required subject, execution, and postcondition observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Integration Validation** is admitted, downstream systems may consume its subject, execution, and postcondition claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Integration Validation** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
