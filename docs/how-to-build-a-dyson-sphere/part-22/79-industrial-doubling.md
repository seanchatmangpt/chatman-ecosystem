# 79. Industrial Doubling

> **Part 22: Scaling Laws.** This part studies the transition from prototypes to astronomical-scale industry. Bottlenecks, queueing, nonlinear interactions, and autonomous local control determine whether scaling laws remain valid.

## Thesis

Industrial Doubling is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

Scaling is governed by bottlenecks and feedback, not by extrapolating one prototype linearly. Little's Law, L=λW, connects work-in-process, throughput, and cycle time; at industrial scale it becomes a way to detect hidden queues in mining, refining, fabrication, transport, verification, and repair. Exponential capacity growth is possible only while each replication cycle closes its scarce inputs and does not saturate another constraint.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Replication Rate](79-01-replication-rate.md)
- [Bottleneck Analysis](79-02-bottleneck-analysis.md)
- [Little's Law](79-03-littles-law.md)
- [Constraint Theory](79-04-constraint-theory.md)
- [Learning Curves](79-05-learning-curves.md)
- [Compounding Capacity](79-06-compounding-capacity.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
