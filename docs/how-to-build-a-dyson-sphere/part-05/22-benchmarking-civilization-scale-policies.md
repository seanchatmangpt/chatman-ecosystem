# Benchmarking Civilization-Scale Policies

> **Subject identity:** `dyson:benchmarking-civilization-scale-policies:d5df78a49011`
> **Domain:** `simulation`
> **Standing of this text:** engineering specification and reasoning surface; **not evidence that a physical Dyson system exists.**

## Why this page exists

**Benchmarking Civilization-Scale Policies** exists because it changes a concrete decision inside **Part V — gymact: Build the Solar System Before Building in It**. It must make the subject operational rather than merely name it: identify state that can be observed, a model or transformation that consumes that state, a constraint that can reject a candidate, and evidence that permits downstream reliance.

For **Benchmarking Civilization-Scale Policies**, the primary state variables include **world state**, **policy**, and **action space**; the control or consequence variables include **observation space**, **scenario**, and **falsifier**. Making those variables explicit prevents this page from collapsing into a slogan and gives later simulation, generation, policy, or verification a typed interface.

The boundary is operational, not literary. Inputs to **Benchmarking Civilization-Scale Policies** must belong to an exact subject and outputs must be consumable by a downstream calculation, validator, simulation, factory, policy engine, or verifier. An output that cannot change any downstream decision is documentation, not manufactured capability.

## Decomposition

- [Throughput](22-01-throughput.md)
- [Yield](22-02-yield.md)
- [Energy Return](22-03-energy-return.md)
- [Material Efficiency](22-04-material-efficiency.md)
- [Fault Recovery](22-05-fault-recovery.md)
- [Reversibility](22-06-reversibility.md)
- [Safety](22-07-safety.md)
- [Receipt Completeness](22-08-receipt-completeness.md) For **Benchmarking Civilization-Scale Policies**, this reusable domain rule is evaluated against `dyson:benchmarking-civilization-scale-policies:d5df78a49011`; its observations, validity interval, constraints, and downstream consumer remain specific to this page even when the underlying law is shared.

## Engineering model

**Benchmarking Civilization-Scale Policies** is an experiment over an explicit world. Define an episode as

\[
E=W\times R\times P\times O\times A\times I\times Auth
\]

for world state, roles, policies, observation projection, action projection, information partitions, and authority. `dyson:benchmarking-civilization-scale-policies:d5df78a49011` is informative only when it names the assumption being stressed and a falsifier capable of rejecting the policy. Simulation standing belongs to the simulated subject, not the physical system.

## Operational contract

| Surface | Required content | Why it matters |
|---|---|---|
| Exact subject | `dyson:benchmarking-civilization-scale-policies:d5df78a49011` plus revision/epoch/environment | prevents standing transfer to a merely similar object |
| Inputs | world state, policy, action space with unit/schema and provenance | makes reasoning reproducible and uncertainty visible |
| Outputs | observation space, scenario or typed refusal | makes prose actionable downstream |
| Invariants | named physical, semantic, safety, or authority constraints | makes counterexamples executable |
| Consequence | SELECT, CONSTRUCT, or brokered DO | prevents intelligence from silently becoming authority |
| Verification | measurable postcondition + owning verifier | separates execution from evidence-backed standing |

## Worked reasoning

For **Benchmarking Civilization-Scale Policies**, Pair every nominal scenario with an adversarial neighbor that changes one assumption. Outcome differences expose which assumption actually supports the policy.

## Questions the design must answer

1. For **Benchmarking Civilization-Scale Policies**: Which world assumptions make the scenario informative?
2. For **Benchmarking Civilization-Scale Policies**: Which policy outcome is a falsifier rather than a tuning opportunity?
3. For **Benchmarking Civilization-Scale Policies**: How is simulation standing prevented from becoming deployment standing?

## Executable representation

```yaml
subject: dyson:benchmarking-civilization-scale-policies:d5df78a49011
topic: "Benchmarking Civilization-Scale Policies"
preconditions: [observed, admitted]
candidate: explicit
constraints: explicit
consequence_path: BRCE_if_DO
postconditions: [measurable, exact_subject]
receipt: required_after_consequence
replay: non_actuating
```

## Failure modes and counterexamples

- One passing world is promoted to physical standing without transfer evidence.
- **Identity drift:** evidence about another revision/environment is silently inherited by **Benchmarking Civilization-Scale Policies**.
- **Hidden assumption:** world state or policy is treated as constant even though the decision depends on it.
- **Evidence collapse:** construction or command success is mistaken for verified consequence without observing the required postcondition.

## DfCM decision rule

For **Benchmarking Civilization-Scale Policies**, preserve all candidates that satisfy current hard constraints even when they are not presently preferred. Rank or select only after recording why alternatives remain lawful, blocked, unsupported, or dominated. Prefer a reversible model change, simulation, or generated artifact before an irreversible physical transition whenever it can answer the same uncertainty. A blocked edge remains topology; it is not deleted to make the plan look complete.

## Admission and authority boundary

```text
OBSERVED -> ADMITTED -> CONSTRUCTED -> (BRCE authority) -> EXECUTED
         -> CHANGED -> VERIFIED -> RECEIPTED -> REPLAYABLE -> STANDING
```

For `dyson:benchmarking-civilization-scale-policies:d5df78a49011`, none of the following imply DO authority: model recommendation, generated file, theorem, simulation pass, telemetry event, credential, or green workflow. Consequential execution requires exact-subject intent plus bounded authority; replay verifies the evidence chain and **must not re-actuate** the consequence.

## Admission test

- [ ] The exact **Benchmarking Civilization-Scale Policies** subject/revision is named.
- [ ] Required world state, policy, and action space observations exist with provenance.
- [ ] Units/schema are machine-checkable and uncertainty/quality is retained.
- [ ] At least one falsifier can reject the candidate.
- [ ] The action class is explicitly SELECT, CONSTRUCT, or DO.
- [ ] Any DO path is brokered, scoped, bounded, and receipted.
- [ ] The owning verifier observes the postcondition against the same subject.
- [ ] Replay reconstructs standing without repeating physical consequence.

## Downstream consequence

When **Benchmarking Civilization-Scale Policies** is admitted, downstream systems may consume its world state, policy, and action space claims only inside their recorded validity bounds. They do **not** inherit authority or standing. A changed subject, stale epoch, failed invariant, or contradictory observation reopens the decision rather than being hidden by regeneration.

## Epistemic boundary

This page makes **Benchmarking Civilization-Scale Policies** more precise; it does not make speculative engineering real. Equations are bounded models, numeric examples are illustrative unless bound to admitted data, simulations are evidence about simulation subjects, and generated artifacts remain candidates until verified. Where measurement, material capability, institutional authority, or physical demonstration is absent, the correct state remains `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED` rather than narrative `ALIVE`.
