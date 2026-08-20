# Phase Four: The First Swarm

> **Subject identity:** `dyson:phase-four-the-first-swarm:5d8aaddcb514`
> **Domain:** `manufacturing`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Phase Four: The First Swarm** exists because it changes a concrete decision inside **Part XI — The Industrial Bootstrap**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Phase Four: The First Swarm**, the primary state variables include **bill of materials**, **process step**, and **yield**; the control or consequence variables include **throughput**, **tooling**, and **quality**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Phase Four: The First Swarm** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Collector 00000001](45-01-collector-00000001.md)
- [First Replication Chain](45-02-first-replication-chain.md)
- [First Gigawatt](45-03-first-gigawatt.md)
- [First Terawatt](45-04-first-terawatt.md)
- [First Petawatt](45-05-first-petawatt.md)
- [Scaling Laws](45-06-scaling-laws.md) For **Phase Four: The First Swarm**, this reusable domain rule is evaluated against `dyson:phase-four-the-first-swarm:5d8aaddcb514`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Phase Four: The First Swarm**, factory closure is a measured transformation:

```text
(feedstock, energy, tooling, robotics)
 -> (qualified product, rework, waste, wear)
```

Yield is measured after inspection and rework, not inferred from nominal cycle rate. `dyson:phase-four-the-first-swarm:5d8aaddcb514` tracks process capability, calibration, critical tooling, spare consumption, batch genealogy, inspection result, and the downstream acceptance criterion that makes output usable.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:phase-four-the-first-swarm:5d8aaddcb514` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | bill of materials, process step, yield with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | throughput, tooling or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Phase Four: The First Swarm**, Distinguish nominal cycle time from qualified-output cycle time. A fast process with poor first-pass yield can have lower effective throughput once inspection and rework are included.

## Questions the design must answer

1. For **Phase Four: The First Swarm**: Which process step is the bottleneck after yield and rework?
2. For **Phase Four: The First Swarm**: Which tooling or calibration dependency prevents false factory closure?
3. For **Phase Four: The First Swarm**: Which quality attribute admits output to the next process?

## Executable representation

```yaml
subject: dyson:phase-four-the-first-swarm:5d8aaddcb514
topic: "Phase Four: The First Swarm"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Phase Four: The First Swarm**.
- **Hidden assumption:** bill of materials or process step is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Phase Four: The First Swarm**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:phase-four-the-first-swarm:5d8aaddcb514`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Phase Four: The First Swarm** subject/revision is named.
- [ ] Required bill of materials, process step, and yield observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Phase Four: The First Swarm** is admitted, downstream systems may consume its bill of materials, process step, and yield claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Phase Four: The First Swarm** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
