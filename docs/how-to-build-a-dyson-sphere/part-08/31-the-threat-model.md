# 31. The Threat Model

> **Part 8: CASTLE: Security for a Stellar Civilization.** This part treats every node, link, model, factory, and key as potentially faulty. Security is built from explicit identity, least authority, attestation, compartmentalization, and replayable evidence.

## Thesis

The Threat Model is treated here as a systems problem rather than an isolated component. At Dyson-swarm scale, a locally sensible decision can become globally unsafe when it hides mass, heat, latency, authority, or evidence. The chapter therefore asks what the object is, what observations are required to reason about it, what constraints delimit its lawful construction space, and what evidence would justify advancing its standing.

Stellar power is the dominant external input. For an approximately isotropic star of luminosity L, irradiance at radius r is F=L/(4πr²). This inverse-square relation turns orbital radius into an energy-density and thermal-design parameter. For the Sun, total luminosity is about 3.8×10^26 W; a civilization need not capture all of it for the industrial consequences to be enormous.

Stellar scale eliminates the plausibility of a trusted interior. Identity, software provenance, key state, policy, and telemetry can all be stale or compromised. CASTLE therefore treats authority as explicit reachability under least privilege, uses content identity and signed evidence where appropriate, partitions failure domains, and never infers permission from network position or possession of a credential.

## Chatman-Ecosystem realization

The operational path is `parse → route → admit/refuse → diagnose/repair → construct → actuate → receipt → replay → standing`. Observation and construction remain maximally expressive above the authority boundary; DO remains narrow. The canonical object is represented in a graph, ggen may render projections, GymAct may execute counterfactuals, Lean/mfact may discharge formal or evidentiary obligations where applicable, and BRCE is the only path permitted to cause a consequential transition.

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

## Chapter map

- [Accidental Failure](31-01-accidental-failure.md)
- [Compromised Nodes](31-02-compromised-nodes.md)
- [Malicious Agents](31-03-malicious-agents.md)
- [Corrupted Models](31-04-corrupted-models.md)
- [Supply-Chain Attacks](31-05-supply-chain-attacks.md)
- [Identity Attacks](31-06-identity-attacks.md)
- [Replay Attacks](31-07-replay-attacks.md)

## Acceptance boundary

This chapter is complete only when its claims can be tied to a bounded subject. A reader should be able to name the observation sources, uncertainty, canonical semantic identity, constraints, reversible candidate space, authority required for consequence, expected postcondition, verifier, and replay path. If any of those are absent, the appropriate state is `UNKNOWN`, `PARTIAL_ALIVE`, `BLOCKED`, or `UNSUPPORTED`—not narrative completion.

## Falsifiers

- A required physical ledger does not close.
- The subject identity is ambiguous or stale.
- A simulation result is presented as physical execution evidence.
- A proof is about a model that was never admitted as the operational subject.
- An actuator can be reached outside the brokered receipt path.
- Replay cannot reconstruct the transition that supposedly established standing.
