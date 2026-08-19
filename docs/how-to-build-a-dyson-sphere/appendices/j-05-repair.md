# Appendix J.5 — Repair

**Parent:** [Appendix J — Civilization-Scale SLOs](j-civilization-scale-slos.md)

AutoFDE is the reality-acquisition and repair loop. It discovers an environment, distinguishes observed capability from assumed capability, constructs candidate repairs, seeks admission, actuates only through the brokered path, and verifies the postcondition against the exact subject. At fleet scale, this loop must remain local-first because communication delay and partition are normal conditions.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
