# Thermal Bounds

**Parent:** [Orbital Invariants](28-orbital-invariants.md)

> **Subject identity:** `dyson:thermal-bounds:ae7e1eead106`
> **Domain:** `thermal`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Thermal Bounds** exists because it changes a concrete decision inside **Orbital Invariants**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Thermal Bounds**, the primary state variables include **radiative flux**, **emissivity**, and **temperature**; the control or consequence variables include **waste heat**, **radiator area**, and **thermal margin**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Thermal Bounds** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Thermal Bounds**, close the heat ledger before optimizing performance:

\[
P_{absorbed}+P_{internal}=P_{export}+P_{stored}+P_{radiated},\qquad
P_{radiated}=\varepsilon\sigma A(T^4-T_{bg}^4).
\] For **Thermal Bounds**, this reusable domain rule is evaluated against `dyson:thermal-bounds:ae7e1eead106`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

The fourth-power temperature term makes hotter radiators smaller in an ideal model, but material limits, electronics lifetime, view factor, degradation, pointing, and local hot spots constrain that option. `dyson:thermal-bounds:ae7e1eead106` is meaningful only when degraded heat rejection is modeled as well as nominal balance.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:thermal-bounds:ae7e1eead106` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | radiative flux, emissivity, temperature with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | waste heat, radiator area or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Thermal Bounds**, Solve both nominal and degraded heat rejection. Loss of radiator area or emissivity should produce a quantitative derating rule rather than an undefined `overheat` state.

## Questions the design must answer

1. For **Thermal Bounds**: Where does every watt ultimately leave the system?
2. For **Thermal Bounds**: Which local component temperature is limiting?
3. For **Thermal Bounds**: How much heat-rejection margin survives degradation and partial shadowing?

## Executable representation

```yaml
subject: dyson:thermal-bounds:ae7e1eead106
topic: "Thermal Bounds"
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

- Fleet-average heat balance closes while a local component exceeds its temperature limit.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Thermal Bounds**.
- **Hidden assumption:** radiative flux or emissivity is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Thermal Bounds**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:thermal-bounds:ae7e1eead106`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Thermal Bounds** subject/revision is named.
- [ ] Required radiative flux, emissivity, and temperature observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Thermal Bounds** is admitted, downstream systems may consume its radiative flux, emissivity, and temperature claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Thermal Bounds** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
