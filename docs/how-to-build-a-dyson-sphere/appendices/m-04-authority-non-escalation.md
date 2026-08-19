# Appendix M.4 — Authority Non-Escalation

**Parent:** [Appendix M — Example Lean Properties](m-example-lean-properties.md)

Formal admission is used only where a machine-checkable invariant can be stated precisely. The critical separation is that rendering, proving, and certifying are different operations: ggen can render a candidate, Lean can discharge a theorem obligation, and mfact can bind evidence to a subject. None of those steps grants DO authority by itself.

SELECT, CONSTRUCT, and DO are separate authority classes. A planner may rank candidates; a constructor may render them; only a brokered authority path may cause consequence. BRCE enforces zero unreceipted actuation by binding intent, subject, authority, preconditions, execution result, postconditions, and replay metadata into a receipt.

## Formalization boundary

The theorem statement must be written over the exact model used by construction. Proving a simplified invariant is useful only if the projection from the operational subject into the theorem model is itself admitted and reviewable.

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
