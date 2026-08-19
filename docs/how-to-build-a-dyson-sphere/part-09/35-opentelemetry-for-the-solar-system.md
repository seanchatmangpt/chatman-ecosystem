# 35. OpenTelemetry for the Solar System

> **Part 9: Weaver: Observe Everything.** This part constructs the observation fabric. Raw signals become useful only after normalization, provenance, subject binding, and admission.

## Thesis

OpenTelemetry for the Solar System is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Signals](35-01-signals.md)
- [Metrics](35-02-metrics.md)
- [Logs](35-03-logs.md)
- [Traces](35-04-traces.md)
- [Events](35-05-events.md)
- [Resources](35-06-resources.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
