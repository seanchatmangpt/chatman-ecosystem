# 50. Stellar Event Sourcing

> **Part 13: The Swarm as a Distributed System.** This part treats the swarm as a delay-tolerant distributed system. Local autonomy is a physical consequence of light-speed latency, not merely a software fashion.

## Thesis

Stellar Event Sourcing is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

A physically credible Dyson program begins with a swarm, not a rigid shell. Independent orbiting collectors can be added incrementally, placed on families of stable trajectories, repaired or retired locally, and diversified by function. A rigid shell around a star has no known passive structural mechanism that keeps it centered; even before material strength is considered, it creates a global stability problem that a swarm avoids.

Stellar power is the dominant external input. For an approximately isotropic star of luminosity L, irradiance at radius r is F=L/(4πr²). This inverse-square relation turns orbital radius into an energy-density and thermal-design parameter. For the Sun, total luminosity is about 3.8×10^26 W; a civilization need not capture all of it for the industrial consequences to be enormous.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

## Governing relation

\[F(r)=\frac{L}{4\pi r^2}\]

The equation is a model boundary, not a complete design. Its variables must be bound to units, provenance, uncertainty, and a validity interval before a downstream system may treat the result as admitted engineering input.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Events as Facts](50-01-events-as-facts.md)
- [OCEL](50-02-ocel.md)
- [Causal Graphs](50-03-causal-graphs.md)
- [Replay](50-04-replay.md)
- [Derived State](50-05-derived-state.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
