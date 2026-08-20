# Compute Is Physical

**Parent:** [Information Physics](17-information-physics.md)

> **Subject identity:** `dyson:compute-is-physical:9adec62c229d`
> **Domain:** `information`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Compute Is Physical** exists because it changes a concrete decision inside **Information Physics**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Compute Is Physical**, the primary state variables include **light-time**, **latency**, and **bandwidth**; the control or consequence variables include **causality**, **clock**, and **consistency**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Compute Is Physical** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Compute Is Physical** is constrained by causality before software preference. One astronomical unit is roughly 499 light-seconds one way, so an interactive round trip across 1 AU inherits about 998 seconds of propagation before queueing or compute. `dyson:compute-is-physical:9adec62c229d` therefore declares freshness tolerance, causal ordering, partition behavior, and the local authority that remains valid while remote coordination is unavailable.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:compute-is-physical:9adec62c229d` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | light-time, latency, bandwidth with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | causality, clock or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Compute Is Physical**, Classify every state field by maximum tolerable age. Millisecond-fresh local attitude and hour-old strategic inventory can coexist; imposing one consistency model either wastes bandwidth or endangers control.

## Questions the design must answer

1. For **Compute Is Physical**: Which decisions require freshness and which tolerate stale but causally ordered state?
2. For **Compute Is Physical**: What information must cross the light-time boundary?
3. For **Compute Is Physical**: What safe local behavior remains during partition?

## Executable representation

```yaml
subject: dyson:compute-is-physical:9adec62c229d
topic: "Compute Is Physical"
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

- A remote coordinator is placed on a safety-critical path whose deadline is shorter than physical light-time permits.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Compute Is Physical**.
- **Hidden assumption:** light-time or latency is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Compute Is Physical**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:compute-is-physical:9adec62c229d`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Compute Is Physical** subject/revision is named.
- [ ] Required light-time, latency, and bandwidth observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Compute Is Physical** is admitted, downstream systems may consume its light-time, latency, and bandwidth claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Compute Is Physical** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
