# Orbital Mechanics

> **Subject identity:** `dyson:orbital-mechanics:9d4cfdac34f6`
> **Domain:** `orbital`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Orbital Mechanics** exists because it changes a concrete decision inside **Part IV — Physics Is the Type System**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Orbital Mechanics**, the primary state variables include **state vector**, **semimajor axis**, and **eccentricity**; the control or consequence variables include **covariance**, **delta-v**, and **conjunction**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Orbital Mechanics** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Two-Body Approximation](13-01-two-body-approximation.md)
- [N-Body Reality](13-02-n-body-reality.md)
- [Keplerian Elements](13-03-keplerian-elements.md)
- [Perturbations](13-04-perturbations.md)
- [Resonances](13-05-resonances.md)
- [Station Keeping](13-06-station-keeping.md)
- [Collision Probability](13-07-collision-probability.md) For **Orbital Mechanics**, this reusable domain rule is evaluated against `dyson:orbital-mechanics:9d4cfdac34f6`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Orbital Mechanics**, start from a state vector and epoch rather than a prose orbit label. In the two-body core, `r` and `v` evolve under gravitational parameter `μ`; useful derived boundaries include

\[
T=2\pi\sqrt{\frac{a^3}{\mu}},\qquad q=a(1-e),\qquad Q=a(1+e).
\]

A flight-relevant `dyson:orbital-mechanics:9d4cfdac34f6` record also carries reference frame, covariance, maneuver history, force-model version, and validity horizon. Perturbations, radiation pressure, multi-body effects, navigation error, and conjunction uncertainty are not optional metadata; they determine when the simple model ceases to support a decision.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:orbital-mechanics:9d4cfdac34f6` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | state vector, semimajor axis, eccentricity with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | covariance, delta-v or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Orbital Mechanics**, Compare nominal, degraded-navigation, and no-maneuver-safe trajectories. A design is stronger when all remain inside protected bounds than when one high-precision nominal solution looks optimal.

## Questions the design must answer

1. For **Orbital Mechanics**: Which approximation regime is valid over the decision horizon?
2. For **Orbital Mechanics**: What state and covariance must be propagated before an orbit-changing command is admissible?
3. For **Orbital Mechanics**: Which perturbation or conjunction invalidates the current trajectory class?

## Executable representation

```yaml
subject: dyson:orbital-mechanics:9d4cfdac34f6
topic: "Orbital Mechanics"
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

- The nominal trajectory is safe while its propagated uncertainty envelope violates a thermal, conjunction, or protected-region bound.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Orbital Mechanics**.
- **Hidden assumption:** state vector or semimajor axis is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Orbital Mechanics**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:orbital-mechanics:9d4cfdac34f6`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Orbital Mechanics** subject/revision is named.
- [ ] Required state vector, semimajor axis, and eccentricity observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Orbital Mechanics** is admitted, downstream systems may consume its state vector, semimajor axis, and eccentricity claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Orbital Mechanics** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
