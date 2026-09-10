# No Ambient Reproduction Authority

**Parent:** [Self-Replication Without Unbounded Replication](26-self-replication-without-unbounded-replication.md)

> **Subject identity:** `dyson:no-ambient-reproduction-authority:0404351e91af`
> **Domain:** `replication`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**No Ambient Reproduction Authority** exists because it changes a concrete decision inside **Self-Replication Without Unbounded Replication**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **No Ambient Reproduction Authority**, the primary state variables include **replication cycle**, **generation limit**, and **mass budget**; the control or consequence variables include **energy budget**, **shutdown**, and **lineage**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **No Ambient Reproduction Authority** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**No Ambient Reproduction Authority** is a bounded population process. An unconstrained toy model can write `C_n=C_0(1+r)^n`, but real growth is limited by feedstock, energy, tooling, transport, verification, repair, and explicit generation limits. `dyson:no-ambient-reproduction-authority:0404351e91af` records lineage, parent receipt, resource budget, allowed generation, orbital/geographic fence, shutdown semantics, and reproduction-specific authority.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:no-ambient-reproduction-authority:0404351e91af` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | replication cycle, generation limit, mass budget with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | energy budget, shutdown or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **No Ambient Reproduction Authority**, Compute one full generation through feedstock, tooling wear, energy, verification, spares, and waste. Only surplus after restoring consumed productive capital is available for growth.

## Questions the design must answer

1. For **No Ambient Reproduction Authority**: Which scarce input bounds one complete generation?
2. For **No Ambient Reproduction Authority**: Which generation/orbital/authority limits prevent open-ended reproduction?
3. For **No Ambient Reproduction Authority**: What lineage makes defective descendants traceable?

## Executable representation

```yaml
subject: dyson:no-ambient-reproduction-authority:0404351e91af
topic: "No Ambient Reproduction Authority"
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
- **Identity drift:** evidence about another revision/environment is silently inherited by **No Ambient Reproduction Authority**.
- **Hidden assumption:** replication cycle or generation limit is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **No Ambient Reproduction Authority**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:no-ambient-reproduction-authority:0404351e91af`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **No Ambient Reproduction Authority** subject/revision is named.
- [ ] Required replication cycle, generation limit, and mass budget observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **No Ambient Reproduction Authority** is admitted, downstream systems may consume its replication cycle, generation limit, and mass budget claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **No Ambient Reproduction Authority** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
