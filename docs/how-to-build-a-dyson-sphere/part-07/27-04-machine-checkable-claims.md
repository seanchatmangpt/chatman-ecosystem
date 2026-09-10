# Machine-Checkable Claims

**Parent:** [ggen Renders, Lean Admits, mfact Certifies](27-ggen-renders-lean-admits-mfact-certifies.md)

> **Subject identity:** `dyson:machine-checkable-claims:4822fafb7adb`
> **Domain:** `formal`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Machine-Checkable Claims** exists because it changes a concrete decision inside **ggen Renders, Lean Admits, mfact Certifies**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Machine-Checkable Claims**, the primary state variables include **precondition**, **postcondition**, and **invariant**; the control or consequence variables include **theorem**, **counterexample**, and **exact subject**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Machine-Checkable Claims** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Machine-Checkable Claims**, formalization separates assumptions from proposition before proof:

```text
Given: exact subject S, admitted observations O*, constraints C
Construct: candidate x
Prove: C(S,x) => invariant(S,x)
Exclude: assumptions not represented by C
```

A theorem about a simplified model can be valid while the physical design remains `UNKNOWN`. `dyson:machine-checkable-claims:4822fafb7adb` binds theorem identity, model version, assumptions, result, and the exact artifact whose admission consumes that result.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:machine-checkable-claims:4822fafb7adb` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | precondition, postcondition, invariant with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | theorem, counterexample or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Machine-Checkable Claims**, Write the theorem statement before the proof. If subject, assumptions, and invariant cannot be named precisely, formal tooling cannot rescue the ambiguity; the correct state is an unready obligation.

## Questions the design must answer

1. For **Machine-Checkable Claims**: What proposition is actually proved?
2. For **Machine-Checkable Claims**: Does it refer to the exact admitted subject or a model class?
3. For **Machine-Checkable Claims**: Which counterexample must fail admission?

## Executable representation

```yaml
subject: dyson:machine-checkable-claims:4822fafb7adb
topic: "Machine-Checkable Claims"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Machine-Checkable Claims**.
- **Hidden assumption:** precondition or postcondition is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Machine-Checkable Claims**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:machine-checkable-claims:4822fafb7adb`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Machine-Checkable Claims** subject/revision is named.
- [ ] Required precondition, postcondition, and invariant observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Machine-Checkable Claims** is admitted, downstream systems may consume its precondition, postcondition, and invariant claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Machine-Checkable Claims** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
