# Appendix I — Failure Catalogue

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

Telemetry is raw observation, not standing. Weaver normalizes signals into semantic conventions, attaches resource identity and provenance, and forwards only bounded observations into admission. This avoids a common observability error: turning a successful scrape, log line, or span into a claim that the physical subject behaved correctly.

Failure is modeled as topology rather than surprise. The design objective is to keep a local defect from becoming a global loss: isolate failure domains, preserve safe trajectories, maintain independent shutdown, keep repair paths, and record enough event history for reconstruction. A failed collector should reduce capacity, not invalidate the entire swarm.

## Sections

- [Observation Failures](i-01-observation-failures.md)
- [Admission Failures](i-02-admission-failures.md)
- [Construction Failures](i-03-construction-failures.md)
- [Actuation Failures](i-04-actuation-failures.md)
- [Verification Failures](i-05-verification-failures.md)
- [Authority Failures](i-06-authority-failures.md)
