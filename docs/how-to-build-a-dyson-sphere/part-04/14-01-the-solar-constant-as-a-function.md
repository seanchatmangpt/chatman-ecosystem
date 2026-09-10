# The Solar Constant as a Function

**Parent:** [Energy](14-energy.md)

> **Subject identity:** `dyson:the-solar-constant-as-a-function:a6b063c8b465`
> **Domain:** `energy`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**The Solar Constant as a Function** exists because it changes a concrete decision inside **Energy**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **The Solar Constant as a Function**, the primary state variables include **power balance**, **efficiency**, and **storage**; the control or consequence variables include **transmission**, **dispatch**, and **load**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **The Solar Constant as a Function** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**The Solar Constant as a Function** must name the power boundary being measured. For a serial chain,

\[
P_{delivered}=P_{incident}\prod_i\eta_i,\qquad P_{loss}=P_{incident}-P_{delivered}.
\]

Loss must reappear as heat, reflected/radiated power, stored energy, curtailment, or another explicit channel. `dyson:the-solar-constant-as-a-function:a6b063c8b465` distinguishes incident, converted, routed, stored, delivered, curtailed, and dissipated energy so a nameplate figure cannot masquerade as useful capacity.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:the-solar-constant-as-a-function:a6b063c8b465` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | power balance, efficiency, storage with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | transmission, dispatch or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **The Solar Constant as a Function**, Inverse-square scaling gives four times the ideal irradiance at 0.5 AU relative to 1 AU and one quarter at 2 AU. The same change affects thermal load, degradation, safe modes, and radiator sizing; “more sunlight” is therefore not an unconditional optimization target.

## Questions the design must answer

1. For **The Solar Constant as a Function**: Is the ledger reporting collected, converted, delivered, or useful power?
2. For **The Solar Constant as a Function**: Which stage dominates total loss?
3. For **The Solar Constant as a Function**: What reserve and load-shedding policy contains local failure?

## Executable representation

```yaml
subject: dyson:the-solar-constant-as-a-function:a6b063c8b465
topic: "The Solar Constant as a Function"
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

- Nameplate collection is counted as useful delivered energy and conversion/transmission/storage losses vanish from the ledger.
- **Identity drift:** evidence about another revision/environment is silently inherited by **The Solar Constant as a Function**.
- **Hidden assumption:** power balance or efficiency is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **The Solar Constant as a Function**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:the-solar-constant-as-a-function:a6b063c8b465`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **The Solar Constant as a Function** subject/revision is named.
- [ ] Required power balance, efficiency, and storage observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **The Solar Constant as a Function** is admitted, downstream systems may consume its power balance, efficiency, and storage claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **The Solar Constant as a Function** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
