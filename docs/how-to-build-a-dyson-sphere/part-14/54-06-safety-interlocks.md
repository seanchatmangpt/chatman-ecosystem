# Safety Interlocks

**Parent:** [Beamed Power](54-beamed-power.md)

> **Subject identity:** `dyson:safety-interlocks:7c9453692b6c`
> **Domain:** `safety`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Safety Interlocks** exists because it changes a concrete decision inside **Beamed Power**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Safety Interlocks**, the primary state variables include **hazard**, **safe state**, and **interlock**; the control or consequence variables include **containment**, **trip condition**, and **recovery**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Safety Interlocks** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Engineering model

**Safety Interlocks** is represented as a hazard-control argument:

```text
hazard -> initiating condition -> propagation path -> independent guard
       -> safe state -> recovery criteria -> replayable incident evidence
```

The guard must not share the initiating failure. `dyson:safety-interlocks:7c9453692b6c` names a trip observation, bounded safe state, independently reachable shutdown/avoidance path, and the evidence required before normal operation may resume.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:safety-interlocks:7c9453692b6c` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | hazard, safe state, interlock with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | containment, trip condition or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Safety Interlocks**, Inject the initiating fault while the normal controller is unavailable. If the independent guard cannot still reach the safe state, the protection has a shared failure mode.

## Questions the design must answer

1. For **Safety Interlocks**: What hazard is prevented and what is the independently reachable safe state?
2. For **Safety Interlocks**: Which single failure must not become existential?
3. For **Safety Interlocks**: What observation trips the interlock?

## Executable representation

```yaml
subject: dyson:safety-interlocks:7c9453692b6c
topic: "Safety Interlocks"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- The shutdown path shares power, software, sensor, or authority dependencies with the initiating fault.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Safety Interlocks**.
- **Hidden assumption:** hazard or safe state is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Safety Interlocks**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:safety-interlocks:7c9453692b6c`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Safety Interlocks** subject/revision is named.
- [ ] Required hazard, safe state, and interlock observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Safety Interlocks** is admitted, downstream systems may consume its hazard, safe state, and interlock claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Safety Interlocks** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
