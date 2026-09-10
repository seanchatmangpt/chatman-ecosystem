# Energy Markets

> **Subject identity:** `dyson:energy-markets:0ea4c107bda4`
> **Domain:** `energy`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Energy Markets** exists because it changes a concrete decision inside **Part XIV — The Energy Internet**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Energy Markets**, the primary state variables include **power balance**, **efficiency**, and **storage**; the control or consequence variables include **transmission**, **dispatch**, and **load**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Energy Markets** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Allocation](55-01-allocation.md)
- [Priority](55-02-priority.md)
- [Scarcity](55-03-scarcity.md)
- [Reserves](55-04-reserves.md)
- [Emergency Capacity](55-05-emergency-capacity.md)
- [Machine-Verifiable Settlement](55-06-machine-verifiable-settlement.md) For **Energy Markets**, this reusable domain rule is evaluated against `dyson:energy-markets:0ea4c107bda4`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

**Energy Markets** must name the power boundary being measured. For a serial chain,

\[
P_{delivered}=P_{incident}\prod_i\eta_i,\qquad P_{loss}=P_{incident}-P_{delivered}.
\]

Loss must reappear as heat, reflected/radiated power, stored energy, curtailment, or another explicit channel. `dyson:energy-markets:0ea4c107bda4` distinguishes incident, converted, routed, stored, delivered, curtailed, and dissipated energy so a nameplate figure cannot masquerade as useful capacity.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:energy-markets:0ea4c107bda4` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | power balance, efficiency, storage with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | transmission, dispatch or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Energy Markets**, An illustrative chain with conversion 0.40, transmission 0.92, and storage round-trip 0.90 delivers `0.40×0.92×0.90 = 0.3312` of incident energy through all three stages. The remaining 66.88% must appear in explicit loss or bypass channels.

## Questions the design must answer

1. For **Energy Markets**: Is the ledger reporting collected, converted, delivered, or useful power?
2. For **Energy Markets**: Which stage dominates total loss?
3. For **Energy Markets**: What reserve and load-shedding policy contains local failure?

## Executable representation

```yaml
subject: dyson:energy-markets:0ea4c107bda4
topic: "Energy Markets"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **Energy Markets**.
- **Hidden assumption:** power balance or efficiency is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Energy Markets**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:energy-markets:0ea4c107bda4`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Energy Markets** subject/revision is named.
- [ ] Required power balance, efficiency, and storage observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Energy Markets** is admitted, downstream systems may consume its power balance, efficiency, and storage claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Energy Markets** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
