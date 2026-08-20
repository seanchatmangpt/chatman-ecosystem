# Asteroids and Minor Bodies

**Parent:** [The Stellar Digital Twin](08-the-stellar-digital-twin.md)

> **Subject identity:** `dyson:asteroids-and-minor-bodies:e5673cd55e31`
> **Domain:** `economics`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Asteroids and Minor Bodies** exists because it changes a concrete decision inside **The Stellar Digital Twin**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Asteroids and Minor Bodies**, the primary state variables include **scarcity**, **ledger**, and **opportunity cost**; the control or consequence variables include **allocation**, **settlement**, and **reserve**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Asteroids and Minor Bodies** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

For **Asteroids and Minor Bodies**, cost is a vector before it is a currency scalar:

\[
C=(m,E,t,\Delta v,compute,risk,authority,opportunity).
\]

`dyson:asteroids-and-minor-bodies:e5673cd55e31` separates reservation, commitment, consumption, verified delivery, waste, and settlement. This exposes designs that appear cheap only because they externalize scarce radiator area, launch capacity, repair burden, ecological risk, or future optionality into another ledger.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:asteroids-and-minor-bodies:e5673cd55e31` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | scarcity, ledger, opportunity cost with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | allocation, settlement or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Asteroids and Minor Bodies**, Compare candidates on mass, energy, time, risk, and reversibility before compressing them into one score. The uncompressed vector exposes which trade a scalar objective hides.

## Questions the design must answer

1. For **Asteroids and Minor Bodies**: Which scarce resource is actually allocated?
2. For **Asteroids and Minor Bodies**: Does settlement distinguish reservation, consumption, and verified delivery?
3. For **Asteroids and Minor Bodies**: Which opportunity cost is hidden by the headline metric?

## Executable representation

```yaml
subject: dyson:asteroids-and-minor-bodies:e5673cd55e31
topic: "Asteroids and Minor Bodies"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Asteroids and Minor Bodies**.
- **Hidden assumption:** scarcity or ledger is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Asteroids and Minor Bodies**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:asteroids-and-minor-bodies:e5673cd55e31`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Asteroids and Minor Bodies** subject/revision is named.
- [ ] Required scarcity, ledger, and opportunity cost observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Asteroids and Minor Bodies** is admitted, downstream systems may consume its scarcity, ledger, and opportunity cost claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Asteroids and Minor Bodies** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
