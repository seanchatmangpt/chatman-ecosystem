# Self-Replication Without Unbounded Replication

> **Subject identity:** `dyson:self-replication-without-unbounded-replica:aa0861f0ae90`
> **Domain:** `replication`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Self-Replication Without Unbounded Replication** exists because it changes a concrete decision inside **Part VI — ggen: Manufacturing the Civilization**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Self-Replication Without Unbounded Replication**, the primary state variables include **replication cycle**, **generation limit**, and **mass budget**; the control or consequence variables include **energy budget**, **shutdown**, and **lineage**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Self-Replication Without Unbounded Replication** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [The Replication Problem](26-01-the-replication-problem.md)
- [No Ambient Reproduction Authority](26-02-no-ambient-reproduction-authority.md)
- [Resource Budgets](26-03-resource-budgets.md)
- [Generation Limits](26-04-generation-limits.md)
- [Geofenced and Orbit-Fenced Replication](26-05-geofenced-and-orbit-fenced-replication.md)
- [Shutdown Semantics](26-06-shutdown-semantics.md)
- [Reproduction Receipts](26-07-reproduction-receipts.md) For **Self-Replication Without Unbounded Replication**, this reusable domain rule is evaluated against `dyson:self-replication-without-unbounded-replica:aa0861f0ae90`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

**Self-Replication Without Unbounded Replication** is a bounded population process. An unconstrained toy model can write `C_n=C_0(1+r)^n`, but real growth is limited by feedstock, energy, tooling, transport, verification, repair, and explicit generation limits. `dyson:self-replication-without-unbounded-replica:aa0861f0ae90` records lineage, parent receipt, resource budget, allowed generation, orbital/geographic fence, shutdown semantics, and reproduction-specific authority.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:self-replication-without-unbounded-replica:aa0861f0ae90` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | replication cycle, generation limit, mass budget with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | energy budget, shutdown or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Self-Replication Without Unbounded Replication**, Compute one full generation through feedstock, tooling wear, energy, verification, spares, and waste. Only surplus after restoring consumed productive capital is available for growth.

## Questions the design must answer

1. For **Self-Replication Without Unbounded Replication**: Which scarce input bounds one complete generation?
2. For **Self-Replication Without Unbounded Replication**: Which generation/orbital/authority limits prevent open-ended reproduction?
3. For **Self-Replication Without Unbounded Replication**: What lineage makes defective descendants traceable?

## Executable representation

```yaml
subject: dyson:self-replication-without-unbounded-replica:aa0861f0ae90
topic: "Self-Replication Without Unbounded Replication"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- A descendant depends on hidden imported tooling, so apparent self-replication is actually an external dependency.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Self-Replication Without Unbounded Replication**.
- **Hidden assumption:** replication cycle or generation limit is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Self-Replication Without Unbounded Replication**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:self-replication-without-unbounded-replica:aa0861f0ae90`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Self-Replication Without Unbounded Replication** subject/revision is named.
- [ ] Required replication cycle, generation limit, and mass budget observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Self-Replication Without Unbounded Replication** is admitted, downstream systems may consume its replication cycle, generation limit, and mass budget claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Self-Replication Without Unbounded Replication** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
