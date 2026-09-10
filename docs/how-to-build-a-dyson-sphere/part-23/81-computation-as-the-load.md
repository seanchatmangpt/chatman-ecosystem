# Computation as the Load

> **Subject identity:** `dyson:computation-as-the-load:d3db8399bb8f`
> **Domain:** `matrioshka`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Computation as the Load** exists because it changes a concrete decision inside **Part XXIII — From Dyson Swarm to Matrioshka Brain**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Computation as the Load**, the primary state variables include **exergy**, **temperature layer**, and **waste heat**; the control or consequence variables include **workload**, **latency**, and **radiator**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Computation as the Load** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Why Compute](81-01-why-compute.md)
- [Energy-to-Compute Conversion](81-02-energy-to-compute-conversion.md)
- [Thermal Constraints](81-03-thermal-constraints.md)
- [Latency Domains](81-04-latency-domains.md) For **Computation as the Load**, this reusable domain rule is evaluated against `dyson:computation-as-the-load:d3db8399bb8f`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Computation as the Load**, nested layers are constrained by exergy and heat rejection, not an illustration of shells. A hotter inner workload exports lower-grade radiation; an outer layer can use part of that flux only if its own conversion and radiator ledger closes. `dyson:computation-as-the-load:d3db8399bb8f` schedules jointly over temperature tolerance, latency, reliability, power, and downstream waste-heat coupling.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:computation-as-the-load:d3db8399bb8f` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | exergy, temperature layer, waste heat with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | workload, latency or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Computation as the Load**, Move one workload to a colder outer layer and account for lower cooling temperature against added communication latency and reduced flux. Optimal placement is workload-specific.

## Questions the design must answer

1. For **Computation as the Load**: Which layer can use remaining exergy rather than merely intercept heat?
2. For **Computation as the Load**: How do latency and heat rejection trade?
3. For **Computation as the Load**: Which thermal coupling makes local optimization globally harmful?

## Executable representation

```yaml
subject: dyson:computation-as-the-load:d3db8399bb8f
topic: "Computation as the Load"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Computation as the Load**.
- **Hidden assumption:** exergy or temperature layer is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Computation as the Load**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:computation-as-the-load:d3db8399bb8f`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Computation as the Load** subject/revision is named.
- [ ] Required exergy, temperature layer, and waste heat observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Computation as the Load** is admitted, downstream systems may consume its exergy, temperature layer, and waste heat claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Computation as the Load** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
