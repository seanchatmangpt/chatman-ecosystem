# Appendix J.2 — Safety

**Parent:** [Appendix J — Civilization-Scale SLOs](j-civilization-scale-slos.md)

The subject is treated as a bounded object in the larger stellar-manufacturing graph. Its inputs, outputs, constraints, failure modes, and evidence obligations must be explicit before the system may generalize from a local success to a reusable class.

## Formalization boundary

The theorem statement must be written over the exact model used by construction. Proving a simplified invariant is useful only if the projection from the operational subject into the theorem model is itself admitted and reviewable.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix J.2 — Safety** is not retained as a label-only reference. This page turns a desirable property into an operational service objective. A useful SLO names the measured subject, numerator, denominator, observation window, sampling method, allowed exclusions, error budget, and consequence of breach. Without those fields a target such as 'safe', 'available', or 'reliable' cannot be falsified and therefore cannot govern an autonomous fleet.

## System contract

Civilization-scale objectives must also define locality. A global average can hide catastrophic regional failure, so availability, safety, energy delivery, manufacturing yield, repair latency, observation freshness, and receipt completeness should be measurable per cell/fleet/authority domain and aggregatable upward. Measurement itself is an admitted process with provenance; telemetry loss is not equivalent to perfect performance.

## Failure modes and falsifiers

A breach should drive a bounded control response rather than an unbounded optimizer. Exhausted error budget can halt expansion, reduce actuation authority, shift capacity to repair, or force a narrower operating envelope. The falsifier is straightforward: construct a trace that violates the stated objective and verify that the control plane detects the breach and takes the declared response.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
