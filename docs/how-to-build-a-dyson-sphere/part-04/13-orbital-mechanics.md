# 13. Orbital Mechanics

> **Part 4: Physics Is the Type System.** This part places physics above software preference. Orbital dynamics, energy, thermodynamics, materials, and information limits act like non-negotiable types that candidate designs must inhabit.

## Thesis

Orbital Mechanics is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth.

## Governing relation

\[T^2 = \frac{4\pi^2 a^3}{\mu}\]

The equation is a model boundary, not a complete design. Its variables must be bound to units, provenance, uncertainty, and a validity interval before a downstream system may treat the result as admitted engineering input.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Two-Body Approximation](13-01-two-body-approximation.md)
- [N-Body Reality](13-02-n-body-reality.md)
- [Keplerian Elements](13-03-keplerian-elements.md)
- [Perturbations](13-04-perturbations.md)
- [Resonances](13-05-resonances.md)
- [Station Keeping](13-06-station-keeping.md)
- [Collision Probability](13-07-collision-probability.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
