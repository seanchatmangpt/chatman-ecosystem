# Appendix I.1 — Observation Failures

**Parent:** [Appendix I — Failure Catalogue](i-failure-catalogue.md)

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix I.1 — Observation Failures** is not retained as a label-only reference. This page belongs to the observation boundary: it explains how a real subject becomes an admitted, replayable description rather than an unqualified bag of facts. Observation is always partial. The carrier must bind exact subject identity, measurement time, source provenance, units, uncertainty, contradiction state, and the dimensions that remain UNKNOWN. A digest identifies the carrier; it does not make the carrier true.

## System contract

The operational sequence is `raw signal -> normalization -> provenance -> contradiction handling -> O* admission`. A value can be syntactically present yet inadmissible because its source is stale, its units are unresolved, or another source contradicts it. The critical rule is that UNKNOWN is preserved as topology. Missing knowledge may remove candidate actions from the lawful frontier, but it cannot be converted into permission merely because a planner prefers progress.

## Failure modes and falsifiers

Falsifiers are identity drift, stale observations reused against a changed subject, loss of provenance, contradictory measurements collapsed without a rule, and a regenerated observation whose digest cannot be reproduced from the same admitted inputs. Any of these lowers standing. The recovery path is re-observation and re-admission, not manual assertion that the old world model is still close enough.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
