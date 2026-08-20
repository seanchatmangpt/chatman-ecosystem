# Appendix I — Failure Catalogue

> **Subject identity:** `dyson:appendix-i-failure-catalogue:b7fd7e6043de`
> **Domain:** `telemetry`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Appendix I — Failure Catalogue** exists because it changes a concrete decision inside **Appendices**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Appendix I — Failure Catalogue**, the primary state variables include **resource identity**, **signal**, and **attribute**; the control or consequence variables include **event**, **trace**, and **provenance**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Appendix I — Failure Catalogue** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Observation Failures](i-01-observation-failures.md)
- [Admission Failures](i-02-admission-failures.md)
- [Construction Failures](i-03-construction-failures.md)
- [Actuation Failures](i-04-actuation-failures.md)
- [Verification Failures](i-05-verification-failures.md)
- [Authority Failures](i-06-authority-failures.md) For **Appendix I — Failure Catalogue**, this reusable domain rule is evaluated against `dyson:appendix-i-failure-catalogue:b7fd7e6043de`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Appendix I — Failure Catalogue**, raw signal is only the first event. The observation path for `dyson:appendix-i-failure-catalogue:b7fd7e6043de` is

```text
raw signal -> normalize unit/schema -> bind resource identity
           -> preserve quality/uncertainty -> admit or refuse
           -> derive operational state
```

A successful scrape demonstrates transport, not subject health. Missing, stale, duplicated, and out-of-order signals retain those qualities instead of being collapsed into a healthy latest-value projection. For **Appendix I — Failure Catalogue**, this reusable domain rule is evaluated against `dyson:appendix-i-failure-catalogue:b7fd7e6043de`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:appendix-i-failure-catalogue:b7fd7e6043de` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | resource identity, signal, attribute with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | event, trace or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Appendix I — Failure Catalogue**, Inject missing, stale, duplicated, and out-of-order signals. Preserve quality and causal metadata rather than normalizing all four into a healthy latest-value gauge.

## Questions the design must answer

1. For **Appendix I — Failure Catalogue**: Which resource identity binds the signal to reality?
2. For **Appendix I — Failure Catalogue**: What normalization preserves provenance and quality?
3. For **Appendix I — Failure Catalogue**: Which missing signal remains UNKNOWN rather than healthy?

## Executable representation

```json
{
  "subject": "dyson:appendix-i-failure-catalogue:b7fd7e6043de",
  "topic": "Appendix I \u2014 Failure Catalogue",
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Appendix I — Failure Catalogue**.
- **Hidden assumption:** resource identity or signal is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Appendix I — Failure Catalogue**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:appendix-i-failure-catalogue:b7fd7e6043de`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Appendix I — Failure Catalogue** subject/revision is named.
- [ ] Required resource identity, signal, and attribute observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Appendix I — Failure Catalogue** is admitted, downstream systems may consume its resource identity, signal, and attribute claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Appendix I — Failure Catalogue** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
