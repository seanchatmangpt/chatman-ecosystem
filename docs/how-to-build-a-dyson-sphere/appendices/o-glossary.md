# Appendix O — Glossary

> **Subject identity:** `dyson:appendix-o-glossary:8c173f7d7017`
> **Domain:** `failure`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Appendix O — Glossary** exists because it changes a concrete decision inside **Appendices**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Appendix O — Glossary**, the primary state variables include **failure mode**, **blast radius**, and **detection**; the control or consequence variables include **isolation**, **recovery**, and **permanent guard**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Appendix O — Glossary** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Appendix O — Glossary**, begin with a causal chain rather than a generic robustness statement. `dyson:appendix-o-glossary:8c173f7d7017` records initiating fault, local effect, propagated effect, detection latency, containment boundary, degraded safe behavior, recovery action, and permanent guard. The objective is not zero faults; it is bounded blast radius plus enough event history to reconstruct the fault before changing the guard.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:appendix-o-glossary:8c173f7d7017` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | failure mode, blast radius, detection with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | isolation, recovery or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Appendix O — Glossary**, Inject the fault, measure detection latency and blast radius, verify degraded-safe behavior, and replay history into diagnosis. Recovery without a permanent guard is incident handling, not learning.

## Questions the design must answer

1. For **Appendix O — Glossary**: What is the smallest containing failure domain?
2. For **Appendix O — Glossary**: How is the fault detected before secondary effects dominate?
3. For **Appendix O — Glossary**: Which permanent guard converts the incident into a future refusal?

## Executable representation

```yaml
subject: dyson:appendix-o-glossary:8c173f7d7017
topic: "Appendix O \u2014 Glossary"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- Recovery restores service but leaves no permanent guard, allowing recurrence.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Appendix O — Glossary**.
- **Hidden assumption:** failure mode or blast radius is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Appendix O — Glossary**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:appendix-o-glossary:8c173f7d7017`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Appendix O — Glossary** subject/revision is named.
- [ ] Required failure mode, blast radius, and detection observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Appendix O — Glossary** is admitted, downstream systems may consume its failure mode, blast radius, and detection claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Appendix O — Glossary** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
