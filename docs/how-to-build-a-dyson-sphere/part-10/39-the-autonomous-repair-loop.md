# The Autonomous Repair Loop

> **Subject identity:** `dyson:the-autonomous-repair-loop:290b9d7c901c`
> **Domain:** `autonomy`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**The Autonomous Repair Loop** exists because it changes a concrete decision inside **Part X — AutoFDE for Autonomous Industry**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **The Autonomous Repair Loop**, the primary state variables include **observe**, **classify**, and **localize**; the control or consequence variables include **construct**, **admit**, and **verify**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **The Autonomous Repair Loop** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Observe](39-01-observe.md)
- [Classify](39-02-classify.md)
- [Localize](39-03-localize.md)
- [Construct](39-04-construct.md)
- [Admit](39-05-admit.md)
- [Actuate](39-06-actuate.md)
- [Verify](39-07-verify.md)
- [Encode the Permanent Guard](39-08-encode-the-permanent-guard.md) For **The Autonomous Repair Loop**, this reusable domain rule is evaluated against `dyson:the-autonomous-repair-loop:290b9d7c901c`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

For **The Autonomous Repair Loop**, autonomy is staged rather than ambient:

```text
OBSERVE -> CLASSIFY -> LOCALIZE -> PRESERVE -> CONSTRUCT
        -> ADMIT -> external DO -> VERIFY -> PERMANENT GUARD
```

Each arrow changes evidence type. `dyson:the-autonomous-repair-loop:290b9d7c901c` may discover and rank repairs autonomously, but mutation still needs admitted authority. The loop closes only when the postcondition is observed against the same subject and a durable guard prevents silent recurrence of the defect class.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:the-autonomous-repair-loop:290b9d7c901c` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | observe, classify, localize with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | construct, admit or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **The Autonomous Repair Loop**, Record the preserved repair frontier before selection. If the preferred repair becomes inadmissible, another lawful candidate remains available without rediscovering the state space.

## Questions the design must answer

1. For **The Autonomous Repair Loop**: What observation triggers the loop?
2. For **The Autonomous Repair Loop**: Which candidate repair maximizes reversible relief?
3. For **The Autonomous Repair Loop**: What measured postcondition closes the repair?

## Executable representation

```yaml
subject: dyson:the-autonomous-repair-loop:290b9d7c901c
topic: "The Autonomous Repair Loop"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- The planner's diagnostic capability is allowed to imply mutation authority.
- **Identity drift:** evidence about another revision/environment is silently inherited by **The Autonomous Repair Loop**.
- **Hidden assumption:** observe or classify is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **The Autonomous Repair Loop**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:the-autonomous-repair-loop:290b9d7c901c`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **The Autonomous Repair Loop** subject/revision is named.
- [ ] Required observe, classify, and localize observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **The Autonomous Repair Loop** is admitted, downstream systems may consume its observe, classify, and localize claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **The Autonomous Repair Loop** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
