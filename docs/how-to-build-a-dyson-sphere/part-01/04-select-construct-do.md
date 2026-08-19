# 4. SELECT, CONSTRUCT, DO

> **Part 1: The Dyson Sphere as a Manufacturing Problem.** The opening part reframes the megastructure as a lawful manufacturing system. The reader is asked to stop imagining one impossible construction event and instead model a compounding sequence of bounded industrial transitions.

## Thesis

SELECT, CONSTRUCT, DO is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

A physically credible Dyson program begins with a swarm, not a rigid shell. Independent orbiting collectors can be added incrementally, placed on families of stable trajectories, repaired or retired locally, and diversified by function. A rigid shell around a star has no known passive structural mechanism that keeps it centered; even before material strength is considered, it creates a global stability problem that a swarm avoids.

Factory design is a closure problem: feedstock, energy, tooling, calibration, control, spares, maintenance, waste, and output quality must all be represented. Self-replication is especially dangerous to leave implicit. Reproduction therefore consumes explicit material and energy budgets, generation limits, geographic or orbital fences, shutdown semantics, and receipts for each authorized replication transition.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Three Different Kinds of Authority](04-01-three-different-kinds-of-authority.md)
- [SELECT](04-02-select.md)
- [CONSTRUCT](04-03-construct.md)
- [DO](04-04-do.md)
- [Why Models Do Not Get Ambient Actuation Authority](04-05-why-models-do-not-get-ambient-actuation-authority.md)
- [BRCE: Zero Unreceipted Actuation](04-06-brce-zero-unreceipted-actuation.md)
- [Hooks Manufacture Intents, Not Actions](04-07-hooks-manufacture-intents-not-actions.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
