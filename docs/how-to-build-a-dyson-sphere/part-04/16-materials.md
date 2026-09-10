# Materials

> **Subject identity:** `dyson:materials:be48a36919a5`
> **Domain:** `materials`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Materials** exists because it changes a concrete decision inside **Part IV — Physics Is the Type System**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Materials**, the primary state variables include **mass balance**, **feedstock**, and **yield**; the control or consequence variables include **composition**, **recycling**, and **loss**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Materials** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Mass Is the Primary Budget](16-01-mass-is-the-primary-budget.md)
- [Metals](16-02-metals.md)
- [Silicates](16-03-silicates.md)
- [Carbon](16-04-carbon.md)
- [Volatiles](16-05-volatiles.md)
- [Semiconductors](16-06-semiconductors.md)
- [Radiation Damage](16-07-radiation-damage.md)
- [Fatigue and Lifetime](16-08-fatigue-and-lifetime.md) For **Materials**, this reusable domain rule is evaluated against `dyson:materials:be48a36919a5`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Materials**, conservation is the first refusal boundary:

\[
m_{feed}=m_{product}+m_{recycle}+m_{inventory}+m_{waste}+m_{loss}.
\]

Gross mass is not qualified material. Composition, phase, impurity, process yield, tooling wear, recyclable fraction, and batch genealogy determine whether feedstock can become the intended artifact. `dyson:materials:be48a36919a5` keeps unexplained residual mass visible rather than normalizing it away.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:materials:be48a36919a5` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | mass balance, feedstock, yield with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | composition, recycling or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Materials**, Run the mass ledger on one representative batch and force every residual into qualified product, recoverable material, inventory, known waste, or investigated loss. Scaling unexplained residuals scales uncertainty too.

## Questions the design must answer

1. For **Materials**: Does mass close from characterized feedstock to product, recycle, inventory, waste, and loss?
2. For **Materials**: Which impurity controls yield or lifetime?
3. For **Materials**: Which imported tool prevents false local closure?

## Executable representation

```yaml
subject: dyson:materials:be48a36919a5
topic: "Materials"
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

- Gross feedstock mass is mistaken for qualified material while impurity, yield, tooling, or recycling losses are omitted.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Materials**.
- **Hidden assumption:** mass balance or feedstock is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Materials**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:materials:be48a36919a5`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Materials** subject/revision is named.
- [ ] Required mass balance, feedstock, and yield observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Materials** is admitted, downstream systems may consume its mass balance, feedstock, and yield claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Materials** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
