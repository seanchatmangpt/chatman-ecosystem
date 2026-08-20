# Radio

**Parent:** [Communication Topology](52-communication-topology.md)

> **Subject identity:** `dyson:radio:b3696ef10f3c`
> **Domain:** `distributed`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Radio** exists because it changes a concrete decision inside **Communication Topology**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Radio**, the primary state variables include **partition**, **causal order**, and **local state**; the control or consequence variables include **reconciliation**, **delay tolerance**, and **quorum**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Radio** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Radio** assumes partition and propagation delay are ordinary. Each consequential event needs unique identity, local causal context, exact subject revision, and an idempotency rule. Reconciliation merges facts; it cannot undo duplicate physical consequence. `dyson:radio:b3696ef10f3c` therefore distinguishes append-only history from derived state, and replay rebuilds projections without reissuing commands.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:radio:b3696ef10f3c` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | partition, causal order, local state with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | reconciliation, delay tolerance or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Radio**, Replay the same event twice and partition replicas before reconciliation. Correct behavior requires idempotent consequence and deterministic projection rebuild; duplicate physical actuation is a hard failure.

## Questions the design must answer

1. For **Radio**: Which state must be strongly ordered locally and which can reconcile eventually?
2. For **Radio**: How does safe behavior survive partition and delay?
3. For **Radio**: What event identity prevents duplicate consequence?

## Executable representation

```yaml
subject: dyson:radio:b3696ef10f3c
topic: "Radio"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- Retry after timeout repeats physical consequence because event identity is not idempotent.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Radio**.
- **Hidden assumption:** partition or causal order is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Radio**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:radio:b3696ef10f3c`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Radio** subject/revision is named.
- [ ] Required partition, causal order, and local state observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Radio** is admitted, downstream systems may consume its partition, causal order, and local state claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Radio** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
