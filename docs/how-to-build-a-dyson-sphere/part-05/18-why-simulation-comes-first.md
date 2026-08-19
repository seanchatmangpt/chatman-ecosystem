# 18. Why Simulation Comes First

> **Part 5: gymact: Build the Solar System Before Building in It.** This part creates an experimental world in GymAct. Counterfactual execution is used to eliminate unsafe or incoherent policies before authority is ever granted for physical actuation.

## Thesis

Why Simulation Comes First is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

GymAct provides counterfactual execution before physical consequence. A world model names its state, roles, policies, observation projections, action projections, authority, and episode boundaries. Simulation can falsify a candidate or expose missing constraints, but it cannot prove the physical world will behave identically; its standing is experimental evidence, not deployment evidence.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Simulation Is Not Proof](18-01-simulation-is-not-proof.md)
- [Simulation as an Observation Generator](18-02-simulation-as-an-observation-generator.md)
- [Bounded Worlds](18-03-bounded-worlds.md)
- [Falsifiable Scenarios](18-04-falsifiable-scenarios.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
