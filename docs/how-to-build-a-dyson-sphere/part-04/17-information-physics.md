# 17. Information Physics

> **Part 4: Physics Is the Type System.** This part places physics above software preference. Orbital dynamics, energy, thermodynamics, materials, and information limits act like non-negotiable types that candidate designs must inhabit.

## Thesis

Information Physics is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Information processing remains physical. Landauer's principle gives a lower bound kT ln 2 for irreversible bit erasure, while real systems operate far above that limit because memory, communication, control, error correction, and heat removal dominate. At solar-system scale, propagation delay is also constitutional: one astronomical unit is roughly 499 light-seconds, so globally synchronous control loops are structurally inappropriate.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Compute Is Physical](17-01-compute-is-physical.md)
- [Landauer's Limit](17-02-landauers-limit.md)
- [Latency](17-03-latency.md)
- [Bandwidth](17-04-bandwidth.md)
- [Synchronization Without Global Time](17-05-synchronization-without-global-time.md)
- [Eventual Consistency Across AU-Scale Systems](17-06-eventual-consistency-across-au-scale-systems.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
