# Collector

**Parent:** [Semantic Conventions](36-semantic-conventions.md)

> **Subject identity:** `dyson:collector:893994408670`
> **Domain:** `telemetry`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Collector** exists because it changes a concrete decision inside **Semantic Conventions**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Collector**, the primary state variables include **resource identity**, **signal**, and **attribute**; the control or consequence variables include **event**, **trace**, and **provenance**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Collector** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Collector**, raw signal is only the first event. The observation path for `dyson:collector:893994408670` is

```text
raw signal -> normalize unit/schema -> bind resource identity
           -> preserve quality/uncertainty -> admit or refuse
           -> derive operational state
```

A successful scrape demonstrates transport, not subject health. Missing, stale, duplicated, and out-of-order signals retain those qualities instead of being collapsed into a healthy latest-value projection. For **Collector**, this reusable domain rule is evaluated against `dyson:collector:893994408670`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:collector:893994408670` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | resource identity, signal, attribute with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | event, trace or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Collector**, Inject missing, stale, duplicated, and out-of-order signals. Preserve quality and causal metadata rather than normalizing all four into a healthy latest-value gauge.

## Questions the design must answer

1. For **Collector**: Which resource identity binds the signal to reality?
2. For **Collector**: What normalization preserves provenance and quality?
3. For **Collector**: Which missing signal remains UNKNOWN rather than healthy?

## Executable representation

```json
{
  "subject": "dyson:collector:893994408670",
  "topic": "Collector",
  "state": "OBSERVED_OR_PROPOSED",
  "provenance": "required",
  "unit_or_schema": "required",
  "uncertainty_or_quality": "required",
  "validity": "bounded",
  "consumer": "named downstream admission rule"
}
```

## Failure modes and counterexamples

- Missing data becomes a healthy default, suppressing uncertainty that should trigger investigation.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Collector**.
- **Hidden assumption:** resource identity or signal is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Collector**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:collector:893994408670`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Collector** subject/revision is named.
- [ ] Required resource identity, signal, and attribute observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Collector** is admitted, downstream systems may consume its resource identity, signal, and attribute claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Collector** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
