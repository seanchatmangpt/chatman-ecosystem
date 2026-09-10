# Nested Thermal Layers

> **Subject identity:** `dyson:nested-thermal-layers:9eacf53f4879`
> **Domain:** `matrioshka`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Nested Thermal Layers** exists because it changes a concrete decision inside **Part XXIII — From Dyson Swarm to Matrioshka Brain**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Nested Thermal Layers**, the primary state variables include **exergy**, **temperature layer**, and **waste heat**; the control or consequence variables include **workload**, **latency**, and **radiator**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Nested Thermal Layers** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Hot Inner Compute](82-01-hot-inner-compute.md)
- [Intermediate Layers](82-02-intermediate-layers.md)
- [Cold Outer Compute](82-03-cold-outer-compute.md)
- [Waste-Heat Cascades](82-04-waste-heat-cascades.md) For **Nested Thermal Layers**, this reusable domain rule is evaluated against `dyson:nested-thermal-layers:9eacf53f4879`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Nested Thermal Layers**, nested layers are constrained by exergy and heat rejection, not an illustration of shells. A hotter inner workload exports lower-grade radiation; an outer layer can use part of that flux only if its own conversion and radiator ledger closes. `dyson:nested-thermal-layers:9eacf53f4879` schedules jointly over temperature tolerance, latency, reliability, power, and downstream waste-heat coupling.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:nested-thermal-layers:9eacf53f4879` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | exergy, temperature layer, waste heat with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | workload, latency or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Nested Thermal Layers**, Move one workload to a colder outer layer and account for lower cooling temperature against added communication latency and reduced flux. Optimal placement is workload-specific.

## Questions the design must answer

1. For **Nested Thermal Layers**: Which layer can use remaining exergy rather than merely intercept heat?
2. For **Nested Thermal Layers**: How do latency and heat rejection trade?
3. For **Nested Thermal Layers**: Which thermal coupling makes local optimization globally harmful?

## Executable representation

```yaml
subject: dyson:nested-thermal-layers:9eacf53f4879
topic: "Nested Thermal Layers"
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

- An outer layer is credited with useful energy without closing conversion, communication, and heat rejection.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Nested Thermal Layers**.
- **Hidden assumption:** exergy or temperature layer is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Nested Thermal Layers**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:nested-thermal-layers:9eacf53f4879`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Nested Thermal Layers** subject/revision is named.
- [ ] Required exergy, temperature layer, and waste heat observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Nested Thermal Layers** is admitted, downstream systems may consume its exergy, temperature layer, and waste heat claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Nested Thermal Layers** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
