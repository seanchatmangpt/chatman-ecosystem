# Appendix I.5 — Verification Failures

**Parent:** [Appendix I — Failure Catalogue](i-failure-catalogue.md)

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
