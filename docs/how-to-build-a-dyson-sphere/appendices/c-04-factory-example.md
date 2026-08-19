# Appendix C.4 — Factory Example

**Parent:** [Appendix C — Dyson O*.toml](c-dyson-o-star-toml.md)

A physically credible Dyson program begins with a swarm, not a rigid shell. Independent orbiting collectors can be added incrementally, placed on families of stable trajectories, repaired or retired locally, and diversified by function. A rigid shell around a star has no known passive structural mechanism that keeps it centered; even before material strength is considered, it creates a global stability problem that a swarm avoids.

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

Factory design is a closure problem: feedstock, energy, tooling, calibration, control, spares, maintenance, waste, and output quality must all be represented. Self-replication is especially dangerous to leave implicit. Reproduction therefore consumes explicit material and energy budgets, generation limits, geographic or orbital fences, shutdown semantics, and receipts for each authorized replication transition.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
