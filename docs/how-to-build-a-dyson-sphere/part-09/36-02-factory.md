# Factory

**Parent:** [Semantic Conventions](36-semantic-conventions.md)

> **Subject identity:** `dyson:factory:30b39849bf7e`
> **Domain:** `manufacturing`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Factory** exists because it changes a concrete decision inside **Semantic Conventions**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Factory**, the primary state variables include **bill of materials**, **process step**, and **yield**; the control or consequence variables include **throughput**, **tooling**, and **quality**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Factory** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Factory**, factory closure is a measured transformation:

```text
(feedstock, energy, tooling, robotics)
 -> (qualified product, rework, waste, wear)
```

Yield is measured after inspection and rework, not inferred from nominal cycle rate. `dyson:factory:30b39849bf7e` tracks process capability, calibration, critical tooling, spare consumption, batch genealogy, inspection result, and the downstream acceptance criterion that makes output usable.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:factory:30b39849bf7e` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | bill of materials, process step, yield with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | throughput, tooling or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Factory**, Distinguish nominal cycle time from qualified-output cycle time. A fast process with poor first-pass yield can have lower effective throughput once inspection and rework are included.

## Questions the design must answer

1. For **Factory**: Which process step is the bottleneck after yield and rework?
2. For **Factory**: Which tooling or calibration dependency prevents false factory closure?
3. For **Factory**: Which quality attribute admits output to the next process?

## Executable representation

```yaml
subject: dyson:factory:30b39849bf7e
topic: "Factory"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- Throughput is reported before inspection/rework and scaling amplifies poor yield.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Factory**.
- **Hidden assumption:** bill of materials or process step is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Factory**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:factory:30b39849bf7e`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Factory** subject/revision is named.
- [ ] Required bill of materials, process step, and yield observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Factory** is admitted, downstream systems may consume its bill of materials, process step, and yield claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Factory** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
