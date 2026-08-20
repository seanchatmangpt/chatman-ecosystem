# Extract the Class

**Parent:** [Instance Closure to Class Closure](61-instance-closure-to-class-closure.md)

> **Subject identity:** `dyson:extract-the-class:3de334560032`
> **Domain:** `ecosystem`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Extract the Class** exists because it changes a concrete decision inside **Instance Closure to Class Closure**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Extract the Class**, the primary state variables include **graph**, **projection**, and **admission**; the control or consequence variables include **actuation**, **receipt**, and **standing**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Extract the Class** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Extract the Class**, the Chatman Ecosystem is a correspondence between evidence types rather than one runtime. `dyson:extract-the-class:3de334560032` moves through canonical semantic identity, generated projection, validation/simulation, brokered consequence, receipt, and standing. Each component owns a bounded morphism; none may convert “I can describe it” into “I may do it.”

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:extract-the-class:3de334560032` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | graph, projection, admission with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | actuation, receipt or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Extract the Class**, Trace one fact end to end: graph identity -> generated projection -> verifier -> brokered change -> receipt -> standing. If adjacent stages use different subjects, the pipeline has semantic drift.

## Questions the design must answer

1. For **Extract the Class**: Which component owns this transition?
2. For **Extract the Class**: What canonical graph fact drives the projection?
3. For **Extract the Class**: Which receipt proves the exact-subject transition?

## Executable representation

```yaml
subject: dyson:extract-the-class:3de334560032
topic: "Extract the Class"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- One component collapses observation, construction, actuation, and standing into an unauditable shortcut.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Extract the Class**.
- **Hidden assumption:** graph or projection is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Extract the Class**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:extract-the-class:3de334560032`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Extract the Class** subject/revision is named.
- [ ] Required graph, projection, and admission observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Extract the Class** is admitted, downstream systems may consume its graph, projection, and admission claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Extract the Class** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
