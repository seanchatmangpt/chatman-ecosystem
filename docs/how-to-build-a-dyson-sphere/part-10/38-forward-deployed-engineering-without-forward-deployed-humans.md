# 38. Forward-Deployed Engineering Without Forward-Deployed Humans

> **Part 10: AutoFDE for Autonomous Industry.** This part describes autonomous field engineering as a bounded control loop. Discovery, diagnosis, construction, actuation, and verification remain separate so autonomy does not become ambient authority.

## Thesis

Forward-Deployed Engineering Without Forward-Deployed Humans is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

AutoFDE is the reality-acquisition and repair loop. It discovers an environment, distinguishes observed capability from assumed capability, constructs candidate repairs, seeks admission, actuates only through the brokered path, and verifies the postcondition against the exact subject. At fleet scale, this loop must remain local-first because communication delay and partition are normal conditions.

Abundant inference does not remove the need for authority, proof, physics, or consent. Models can propose, search, summarize, and construct, but their outputs remain unadmitted until tied to a subject and constraint set. Human standing is preserved through explicit objectives, consent, delegation scope, revocation, and refusal rather than vague claims that intelligence implies legitimacy.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Environment Discovery](38-01-environment-discovery.md)
- [Capability Discovery](38-02-capability-discovery.md)
- [Constraint Discovery](38-03-constraint-discovery.md)
- [Plan Construction](38-04-plan-construction.md)
- [Admission](38-05-admission.md)
- [Execution](38-06-execution.md)
- [Verification](38-07-verification.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
