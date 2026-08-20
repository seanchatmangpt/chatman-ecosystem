# Mass Conservation

**Parent:** [Appendix M — Example Lean Properties](m-example-lean-properties.md)

> **Subject identity:** `dyson:mass-conservation:1b15ff03b816`
> **Domain:** `materials`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Mass Conservation** exists because it changes a concrete decision inside **Appendix M — Example Lean Properties**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Mass Conservation**, the primary state variables include **mass balance**, **feedstock**, and **yield**; the control or consequence variables include **composition**, **recycling**, and **loss**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Mass Conservation** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Mass Conservation**, conservation is the first refusal boundary:

\[
m_{feed}=m_{product}+m_{recycle}+m_{inventory}+m_{waste}+m_{loss}.
\]

Gross mass is not qualified material. Composition, phase, impurity, process yield, tooling wear, recyclable fraction, and batch genealogy determine whether feedstock can become the intended artifact. `dyson:mass-conservation:1b15ff03b816` keeps unexplained residual mass visible rather than normalizing it away.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:mass-conservation:1b15ff03b816` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | mass balance, feedstock, yield with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | composition, recycling or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Mass Conservation**, A manufacturing receipt reconciles measured input mass with qualified product, recoverable scrap, process inventory, waste, and loss. A persistent unexplained residual can indicate leakage, sensor drift, theft, or a missing process state; it is evidence to investigate, not a rounding error to suppress.

## Questions the design must answer

1. For **Mass Conservation**: Does mass close from characterized feedstock to product, recycle, inventory, waste, and loss?
2. For **Mass Conservation**: Which impurity controls yield or lifetime?
3. For **Mass Conservation**: Which imported tool prevents false local closure?

## Executable representation

```yaml
subject: dyson:mass-conservation:1b15ff03b816
topic: "Mass Conservation"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Mass Conservation**.
- **Hidden assumption:** mass balance or feedstock is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Mass Conservation**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:mass-conservation:1b15ff03b816`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Mass Conservation** subject/revision is named.
- [ ] Required mass balance, feedstock, and yield observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Mass Conservation** is admitted, downstream systems may consume its mass balance, feedstock, and yield claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Mass Conservation** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
