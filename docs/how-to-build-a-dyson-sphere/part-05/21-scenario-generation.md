# 21. Scenario Generation

> **Part 5: gymact: Build the Solar System Before Building in It.** This part creates an experimental world in GymAct. Counterfactual execution is used to eliminate unsafe or incoherent policies before authority is ever granted for physical actuation.

## Thesis

Scenario Generation is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

ggen is treated as a semantic manufacturing compiler: graph and query select meaning, templates render projections, validators reject malformed output, and receipts bind the generated artifact to the admitted subject. Generation is not evidence of correctness. The value of the generator is reproducibility and class closure—once a construction pattern is admitted, it can be regenerated for new subjects without rediscovering the pattern manually.

GymAct provides counterfactual execution before physical consequence. A world model names its state, roles, policies, observation projections, action projections, authority, and episode boundaries. Simulation can falsify a candidate or expose missing constraints, but it cannot prove the physical world will behave identically; its standing is experimental evidence, not deployment evidence.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Nominal Worlds](21-01-nominal-worlds.md)
- [Rare Events](21-02-rare-events.md)
- [Adversarial Worlds](21-03-adversarial-worlds.md)
- [Sensor Failure](21-04-sensor-failure.md)
- [Communication Failure](21-05-communication-failure.md)
- [Manufacturing Defects](21-06-manufacturing-defects.md)
- [Orbital Cascade Events](21-07-orbital-cascade-events.md)
- [Solar Storms](21-08-solar-storms.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
