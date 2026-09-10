# Appendix J — Civilization-Scale SLOs

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

The subject is treated as a bounded object in the larger stellar-manufacturing graph. Its inputs, outputs, constraints, failure modes, and evidence obligations must be explicit before the system may generalize from a local success to a reusable class.

## Sections

- [Availability](j-01-availability.md)
- [Safety](j-02-safety.md)
- [Energy](j-03-energy.md)
- [Manufacturing](j-04-manufacturing.md)
- [Repair](j-05-repair.md)
- [Observation](j-06-observation.md)
- [Receipt Completeness](j-07-receipt-completeness.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix J — Civilization-Scale SLOs** is not retained as a label-only reference. This page turns a desirable property into an operational service objective. A useful SLO names the measured subject, numerator, denominator, observation window, sampling method, allowed exclusions, error budget, and consequence of breach. Without those fields a target such as 'safe', 'available', or 'reliable' cannot be falsified and therefore cannot govern an autonomous fleet.

## System contract

Civilization-scale objectives must also define locality. A global average can hide catastrophic regional failure, so availability, safety, energy delivery, manufacturing yield, repair latency, observation freshness, and receipt completeness should be measurable per cell/fleet/authority domain and aggregatable upward. Measurement itself is an admitted process with provenance; telemetry loss is not equivalent to perfect performance.

## Failure modes and falsifiers

A breach should drive a bounded control response rather than an unbounded optimizer. Exhausted error budget can halt expansion, reduce actuation authority, shift capacity to repair, or force a narrower operating envelope. The falsifier is straightforward: construct a trace that violates the stated objective and verify that the control plane detects the breach and takes the declared response.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
