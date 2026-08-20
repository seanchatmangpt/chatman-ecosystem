# SUBJECT_ALIVE

**Parent:** [Collector One](100-collector-one.md)

> **Subject identity:** `dyson:subject-alive:8c5a81bb1dff`
> **Domain:** `verification`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**SUBJECT_ALIVE** exists because it changes a concrete decision inside **Collector One**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **SUBJECT_ALIVE**, the primary state variables include **subject**, **execution**, and **postcondition**; the control or consequence variables include **verifier**, **receipt**, and **replay**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **SUBJECT_ALIVE** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **SUBJECT_ALIVE**, standing belongs to an exact subject and revision. The evidence chain is

```text
observed -> admitted -> executed -> changed -> verified -> receipted -> replayable
```

Those predicates are not interchangeable. `dyson:subject-alive:8c5a81bb1dff` reaches `ALIVE` only when the owning verifier observes the required postcondition against the admitted subject and replay reconstructs why the claim was made. A different SHA, environment, world model, or verifier is a different subject.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:subject-alive:8c5a81bb1dff` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | subject, execution, postcondition with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | verifier, receipt or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **SUBJECT_ALIVE**, Change only the subject SHA and rerun receipt lookup. An exact-subject verifier refuses standing inheritance even when the candidate appears behaviorally similar.

## Questions the design must answer

1. For **SUBJECT_ALIVE**: What exact subject executed and what changed?
2. For **SUBJECT_ALIVE**: Which evidence would downgrade standing?
3. For **SUBJECT_ALIVE**: Can replay reconstruct the decision without repeating consequence?

## Executable representation

```yaml
subject: dyson:subject-alive:8c5a81bb1dff
topic: "SUBJECT_ALIVE"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **SUBJECT_ALIVE**.
- **Hidden assumption:** subject or execution is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **SUBJECT_ALIVE**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:subject-alive:8c5a81bb1dff`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **SUBJECT_ALIVE** subject/revision is named.
- [ ] Required subject, execution, and postcondition observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **SUBJECT_ALIVE** is admitted, downstream systems may consume its subject, execution, and postcondition claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **SUBJECT_ALIVE** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
