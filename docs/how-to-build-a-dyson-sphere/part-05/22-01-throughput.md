# Throughput

**Parent:** [Benchmarking Civilization-Scale Policies](22-benchmarking-civilization-scale-policies.md)

> **Subject identity:** `dyson:throughput:6f846ab83999`
> **Domain:** `scaling`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Throughput** exists because it changes a concrete decision inside **Benchmarking Civilization-Scale Policies**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Throughput**, the primary state variables include **throughput**, **work-in-process**, and **cycle time**; the control or consequence variables include **bottleneck**, **utilization**, and **capacity**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Throughput** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Throughput**, throughput is constrained by queues. Little's Law,

\[
L=\lambda W,
\]

connects work-in-process, throughput, and cycle time for a stable process. `dyson:throughput:6f846ab83999` uses it to expose hidden queues in mining, refining, transport, verification, and repair. Exponential fleet counts are inadmissible when a required queue is unstable, yield collapses, or coordination becomes the critical path.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:throughput:6f846ab83999` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | throughput, work-in-process, cycle time with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | bottleneck, utilization or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Throughput**, Increase offered work until one queue becomes unstable. The first diverging queue is stronger evidence of the true constraint than an architecture diagram labeling every component scalable.

## Questions the design must answer

1. For **Throughput**: Which queue grows first as throughput rises?
2. For **Throughput**: Which exponential trend disappears when a downstream constraint saturates?
3. For **Throughput**: What local autonomy removes coordination from the critical path?

## Executable representation

```yaml
subject: dyson:throughput:6f846ab83999
topic: "Throughput"
model:
  regime: explicit
  units: required
  uncertainty: propagated
  validity_horizon: bounded
verification:
  invariant: named
  tolerance: named
  counterexample: required
```

## Failure modes and counterexamples

- Prototype throughput is extrapolated after a downstream queue has become unstable.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Throughput**.
- **Hidden assumption:** throughput or work-in-process is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Throughput**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:throughput:6f846ab83999`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Throughput** subject/revision is named.
- [ ] Required throughput, work-in-process, and cycle time observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Throughput** is admitted, downstream systems may consume its throughput, work-in-process, and cycle time claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Throughput** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
