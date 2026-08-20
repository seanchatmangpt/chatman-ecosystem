# Phase Two: Asteroid Industry

> **Subject identity:** `dyson:phase-two-asteroid-industry:90a101a81d32`
> **Domain:** `economics`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Phase Two: Asteroid Industry** exists because it changes a concrete decision inside **Part XI — The Industrial Bootstrap**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Phase Two: Asteroid Industry**, the primary state variables include **scarcity**, **ledger**, and **opportunity cost**; the control or consequence variables include **allocation**, **settlement**, and **reserve**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Phase Two: Asteroid Industry** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Prospecting](43-01-prospecting.md)
- [Resource Classification](43-02-resource-classification.md)
- [Extraction](43-03-extraction.md)
- [Refinement](43-04-refinement.md)
- [Mass Drivers](43-05-mass-drivers.md)
- [Distributed Manufacturing](43-06-distributed-manufacturing.md) For **Phase Two: Asteroid Industry**, this reusable domain rule is evaluated against `dyson:phase-two-asteroid-industry:90a101a81d32`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Phase Two: Asteroid Industry**, cost is a vector before it is a currency scalar:

\[
C=(m,E,t,\Delta v,compute,risk,authority,opportunity).
\]

`dyson:phase-two-asteroid-industry:90a101a81d32` separates reservation, commitment, consumption, verified delivery, waste, and settlement. This exposes designs that appear cheap only because they externalize scarce radiator area, launch capacity, repair burden, ecological risk, or future optionality into another ledger.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:phase-two-asteroid-industry:90a101a81d32` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | scarcity, ledger, opportunity cost with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | allocation, settlement or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Phase Two: Asteroid Industry**, Compare candidates on mass, energy, time, risk, and reversibility before compressing them into one score. The uncompressed vector exposes which trade a scalar objective hides.

## Questions the design must answer

1. For **Phase Two: Asteroid Industry**: Which scarce resource is actually allocated?
2. For **Phase Two: Asteroid Industry**: Does settlement distinguish reservation, consumption, and verified delivery?
3. For **Phase Two: Asteroid Industry**: Which opportunity cost is hidden by the headline metric?

## Executable representation

```yaml
subject: dyson:phase-two-asteroid-industry:90a101a81d32
topic: "Phase Two: Asteroid Industry"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- A scalar price hides a binding non-monetary constraint such as launch capacity, radiator area, risk, or authority.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Phase Two: Asteroid Industry**.
- **Hidden assumption:** scarcity or ledger is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Phase Two: Asteroid Industry**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:phase-two-asteroid-industry:90a101a81d32`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Phase Two: Asteroid Industry** subject/revision is named.
- [ ] Required scarcity, ledger, and opportunity cost observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Phase Two: Asteroid Industry** is admitted, downstream systems may consume its scarcity, ledger, and opportunity cost claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Phase Two: Asteroid Industry** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
