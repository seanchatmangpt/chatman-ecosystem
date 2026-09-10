# Stellar Classification

**Parent:** [Stellar Observation](05-stellar-observation.md)

> **Subject identity:** `dyson:stellar-classification:36378a70c676`
> **Domain:** `stellar`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Stellar Classification** exists because it changes a concrete decision inside **Stellar Observation**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Stellar Classification**, the primary state variables include **luminosity**, **irradiance**, and **spectrum**; the control or consequence variables include **activity**, **uncertainty**, and **epoch**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Stellar Classification** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Stellar Classification** belongs in a versioned stellar state, not a timeless constant. Ideal irradiance is bounded by

\[
F(r)=\frac{L}{4\pi r^2},
\]

but collector decisions also depend on spectral distribution, activity, variability, geometry, and observation epoch. `dyson:stellar-classification:36378a70c676` must propagate measurement uncertainty into sizing or safety margins instead of substituting a point estimate wherever a range is operationally relevant.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:stellar-classification:36378a70c676` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | luminosity, irradiance, spectrum with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | activity, uncertainty or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Stellar Classification**, Propagate the admitted measurement interval into a downstream sizing or safe-mode choice. If the choice does not change across the range, the design is robust; if it does, more observation has measurable value.

## Questions the design must answer

1. For **Stellar Classification**: Which measured stellar quantities drive the decision, and at what epoch?
2. For **Stellar Classification**: How does uncertainty propagate into collector sizing or safe orbit families?
3. For **Stellar Classification**: Which transient event forces derating or model invalidation?

## Executable representation

```yaml
subject: dyson:stellar-classification:36378a70c676
topic: "Stellar Classification"
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

- A long-lived design treats a stellar estimate as immutable beyond its admitted observation/model horizon.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Stellar Classification**.
- **Hidden assumption:** luminosity or irradiance is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Stellar Classification**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:stellar-classification:36378a70c676`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Stellar Classification** subject/revision is named.
- [ ] Required luminosity, irradiance, and spectrum observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Stellar Classification** is admitted, downstream systems may consume its luminosity, irradiance, and spectrum claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Stellar Classification** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
