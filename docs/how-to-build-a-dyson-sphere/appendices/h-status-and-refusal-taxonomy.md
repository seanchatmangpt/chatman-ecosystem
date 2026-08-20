# Appendix H — Status and Refusal Taxonomy

> **Subject identity:** `dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1`
> **Domain:** `general`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Appendix H — Status and Refusal Taxonomy** exists because it changes a concrete decision inside **Appendices**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Appendix H — Status and Refusal Taxonomy**, the primary state variables include **subject**, **constraint**, and **candidate**; the control or consequence variables include **evidence**, **failure mode**, and **verification**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Appendix H — Status and Refusal Taxonomy** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [UNKNOWN](h-01-unknown.md)
- [PARTIAL_ALIVE](h-02-partial-alive.md)
- [ALIVE](h-03-alive.md)
- [BLOCKED](h-04-blocked.md)
- [BUILD_BROKEN](h-05-build-broken.md)
- [UNSUPPORTED](h-06-unsupported.md)
- [Typed REFUSED](h-07-typed-refused.md) For **Appendix H — Status and Refusal Taxonomy**, this reusable domain rule is evaluated against `dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

**Appendix H — Status and Refusal Taxonomy** is modeled by interfaces rather than by its name. `dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1` identifies consumed observations, produced artifact or decision, hard constraints, reversible candidate space, authority class, expected postcondition, and failure surface. The page is meaningful only when a counterexample can change the resulting decision.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | subject, constraint, candidate with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | evidence, failure mode or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Appendix H — Status and Refusal Taxonomy**, Construct a positive case and a counterexample. If both lead to the same decision, the page has not yet defined a meaningful constraint.

## Questions the design must answer

1. For **Appendix H — Status and Refusal Taxonomy**: What exact subject does this page constrain?
2. For **Appendix H — Status and Refusal Taxonomy**: What reversible candidate space should be preserved?
3. For **Appendix H — Status and Refusal Taxonomy**: What evidence falsifies the working claim?

## Executable representation

```yaml
subject: dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1
topic: "Appendix H \u2014 Status and Refusal Taxonomy"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- The page names a concept but does not change a model, constraint, candidate, verifier, or refusal decision.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Appendix H — Status and Refusal Taxonomy**.
- **Hidden assumption:** subject or constraint is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Appendix H — Status and Refusal Taxonomy**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:appendix-h-status-and-refusal-taxonomy:f467c40846a1`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Appendix H — Status and Refusal Taxonomy** subject/revision is named.
- [ ] Required subject, constraint, and candidate observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Appendix H — Status and Refusal Taxonomy** is admitted, downstream systems may consume its subject, constraint, and candidate claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Appendix H — Status and Refusal Taxonomy** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
