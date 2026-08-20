# Resource Invariants

> **Subject identity:** `dyson:resource-invariants:e9c246b54e48`
> **Domain:** `formal`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Resource Invariants** exists because it changes a concrete decision inside **Part VII — Formal Admission**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Resource Invariants**, the primary state variables include **precondition**, **postcondition**, and **invariant**; the control or consequence variables include **theorem**, **counterexample**, and **exact subject**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Resource Invariants** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Mass Conservation](29-01-mass-conservation.md)
- [Energy Accounting](29-02-energy-accounting.md)
- [Inventory Provenance](29-03-inventory-provenance.md)
- [Waste Accounting](29-04-waste-accounting.md)
- [Closed-Loop Recovery](29-05-closed-loop-recovery.md) For **Resource Invariants**, this reusable domain rule is evaluated against `dyson:resource-invariants:e9c246b54e48`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **Resource Invariants**, formalization separates assumptions from proposition before proof:

```text
Given: exact subject S, admitted observations O*, constraints C
Construct: candidate x
Prove: C(S,x) => invariant(S,x)
Exclude: assumptions not represented by C
```

A theorem about a simplified model can be valid while the physical design remains `UNKNOWN`. `dyson:resource-invariants:e9c246b54e48` binds theorem identity, model version, assumptions, result, and the exact artifact whose admission consumes that result.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:resource-invariants:e9c246b54e48` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | precondition, postcondition, invariant with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | theorem, counterexample or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Resource Invariants**, Write the theorem statement before the proof. If subject, assumptions, and invariant cannot be named precisely, formal tooling cannot rescue the ambiguity; the correct state is an unready obligation.

## Questions the design must answer

1. For **Resource Invariants**: What proposition is actually proved?
2. For **Resource Invariants**: Does it refer to the exact admitted subject or a model class?
3. For **Resource Invariants**: Which counterexample must fail admission?

## Executable representation

```yaml
subject: dyson:resource-invariants:e9c246b54e48
topic: "Resource Invariants"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- A valid theorem is cited for a physical subject whose theorem assumptions were never admitted.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Resource Invariants**.
- **Hidden assumption:** precondition or postcondition is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Resource Invariants**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:resource-invariants:e9c246b54e48`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Resource Invariants** subject/revision is named.
- [ ] Required precondition, postcondition, and invariant observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Resource Invariants** is admitted, downstream systems may consume its precondition, postcondition, and invariant claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Resource Invariants** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
