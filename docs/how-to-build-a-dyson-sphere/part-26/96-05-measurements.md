# Measurements

**Parent:** [Build the Knowledge Graph](96-build-the-knowledge-graph.md)

> **Subject identity:** `dyson:measurements:8fcc659527b4`
> **Domain:** `observation`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Measurements** exists because it changes a concrete decision inside **Build the Knowledge Graph**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Measurements**, the primary state variables include **subject identity**, **source**, and **unit**; the control or consequence variables include **uncertainty**, **epoch**, and **validity interval**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Measurements** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Measurements** becomes `O*` only after it can answer *what, who, how, when, in what unit, with what uncertainty, and for how long*. A deliberately incomplete carrier shows the admission surface:

```toml
subject = "dyson:measurements:8fcc659527b4"
quantity = "measurements"
value_state = "OBSERVED"
unit = "REQUIRED"
uncertainty = "REQUIRED"
observed_at = "REQUIRED"
valid_until = "REQUIRED"
provenance = "REQUIRED"
```

`REQUIRED` is not a placeholder to be guessed. Until real evidence binds those fields, downstream manufacture preserves `UNKNOWN`. For **Measurements**, this reusable domain rule is evaluated against `dyson:measurements:8fcc659527b4`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:measurements:8fcc659527b4` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | subject identity, source, unit with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | uncertainty, epoch or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Measurements**, Store raw observation beside normalized value and transformation receipt. A later calibration update can reproduce the derived value without pretending the original sensor reading changed.

## Questions the design must answer

1. For **Measurements**: Who observed what exact subject, how, when, in what unit, and with what uncertainty?
2. For **Measurements**: When does the observation expire?
3. For **Measurements**: Which contradiction must remain UNKNOWN?

## Executable representation

```json
{
  "subject": "dyson:measurements:8fcc659527b4",
  "topic": "Measurements",
  "state": "OBSERVED_OR_PROPOSED",
  "provenance": "required",
  "unit_or_schema": "required",
  "uncertainty_or_quality": "required",
  "validity": "bounded",
  "consumer": "named downstream admission rule"
}
```

## Failure modes and counterexamples

- A stale or synthetic value is normalized into the same standing as current physical observation.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Measurements**.
- **Hidden assumption:** subject identity or source is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Measurements**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:measurements:8fcc659527b4`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Measurements** subject/revision is named.
- [ ] Required subject identity, source, and unit observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Measurements** is admitted, downstream systems may consume its subject identity, source, and unit claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Measurements** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
