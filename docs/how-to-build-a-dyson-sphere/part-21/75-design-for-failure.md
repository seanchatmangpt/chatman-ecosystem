# 75. Design for Failure

> **Part 21: Failure Engineering.** This part engineers for inevitable failure. The system is designed to contain, reconstruct, learn from, and permanently guard against failure modes without collapsing global capacity.

## Thesis

Design for Failure is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Everything Eventually Fails](75-01-everything-eventually-fails.md)
- [Bounded Failure Domains](75-02-bounded-failure-domains.md)
- [Graceful Degradation](75-03-graceful-degradation.md)
- [Redundancy](75-04-redundancy.md)
- [Repairability](75-05-repairability.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
