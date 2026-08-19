# 28. Orbital Invariants

> **Part 7: Formal Admission.** This part separates generation from admission. Machine-checkable obligations are discharged where possible, and proof evidence is bound to exact subjects instead of treated as ambient truth.

## Thesis

Orbital Invariants is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Orbital state is not a location label; it is a dynamical state with uncertainty. In the two-body approximation, orbital period satisfies T²=4π²a³/μ, where a is semimajor axis and μ is the standard gravitational parameter. Operational designs must then add perturbations, multi-body effects, solar radiation pressure, station-keeping budgets, conjunction probability, and covariance growth.

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

Formal admission is used only where a machine-checkable invariant can be stated precisely. The critical separation is that rendering, proving, and certifying are different operations: ggen can render a candidate, Lean can discharge a theorem obligation, and mfact can bind evidence to a subject. None of those steps grants DO authority by itself.

## Governing relation

\[T^2 = \frac{4\pi^2 a^3}{\mu}\]

The equation is a model boundary, not a complete design. Its variables must be bound to units, provenance, uncertainty, and a validity interval before a downstream system may treat the result as admitted engineering input.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Safe Separation](28-01-safe-separation.md)
- [Periapsis and Apoapsis Bounds](28-02-periapsis-and-apoapsis-bounds.md)
- [Collision Exclusion](28-03-collision-exclusion.md)
- [Thermal Bounds](28-04-thermal-bounds.md)
- [Pointing Constraints](28-05-pointing-constraints.md)
- [Fail-Safe Trajectories](28-06-fail-safe-trajectories.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
