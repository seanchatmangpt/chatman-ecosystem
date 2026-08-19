# Appendix D.5 — Verification Receipt

**Parent:** [Appendix D — Receipt Schemas](d-receipt-schemas.md)

Standing belongs to an exact subject. Inspection is not execution, execution is not verification, and a named receipt file is not evidence that the intended transition occurred. A useful receipt binds identity, authority, consequence, verifier result, and replay instructions so a later observer can reconstruct why the standing claim was made.

## Minimal record

```text
subject = <exact identity>
observed = <bounded inputs>
admitted = <constraints and uncertainty>
authority = <SELECT|CONSTRUCT|DO>
executed = <observed action or NONE>
verified = <postcondition evidence>
receipt = <content identity>
replay = <deterministic reconstruction method>
standing = <bounded status>
```

## Standing rule

The evidentiary vocabulary is deliberately non-binary: `UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, `UNSUPPORTED`, plus typed refusal where a request is understood but not lawfully admissible. `ALIVE` is reserved for observed execution against the exact admitted subject with verifier and replay evidence.
