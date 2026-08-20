# Appendix I.5 — Verification Failures

**Parent:** [Appendix I — Failure Catalogue](i-failure-catalogue.md)

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix I.5 — Verification Failures** is not retained as a label-only reference. Failure is part of the modeled state space, not an exception that disappears from the architecture diagram. This page classifies a particular failure surface so the system can distinguish observation failure, admission refusal, construction defects, actuation ambiguity, verification failure, and authority failure. Those classes demand different recovery behavior and must never be collapsed into a generic retry.

## System contract

The recovery pattern is `detect -> bind exact subject -> classify -> localize -> construct reversible repair -> admit -> actuate if authorized -> observe -> encode permanent guard`. Detection evidence should survive the repair. If the failure involved an ambiguous external effect, reconciliation precedes any new attempt. If it involved invalid authority, no technical workaround is a lawful substitute for obtaining a valid grant.

## Failure modes and falsifiers

A failure catalogue earns its place when every entry has a discriminating signal and a permanent falsifier. Examples include stale pre-state, violated constraint, missing idempotency key, transport timeout after possible actuation, mismatched postcondition, or receipt-integrity failure. The permanent guard should reproduce the original defect and fail before the fix, then pass after it, so the lesson becomes executable knowledge rather than incident folklore.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
