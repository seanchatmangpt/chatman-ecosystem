# Appendix D.1 — Observation Receipt

**Parent:** [Appendix D — Receipt Schemas](d-receipt-schemas.md)

Observation becomes operational only after it is bounded. O* records exact subject identity, source provenance, units, uncertainty, validity interval, contradictions, and exclusions. UNKNOWN is preserved as a value rather than coerced into a guess. This makes later manufacture falsifiable: a design can be traced back to the measurements and assumptions it actually consumed.

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

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix D.1 — Observation Receipt** is not retained as a label-only reference. A receipt is the boundary between an assertion that work happened and evidence that a particular consequential transition has standing. It must bind the exact subject, admitted intent, authority, pre-state, attempted mutation, post-state observation, verifier, outcome, and replay identity. Merely naming a JSON object `receipt` is insufficient; the object has to make substitution and ambiguity mechanically detectable.

## System contract

For consequential DO, reservation precedes actuation. The reservation binds the candidate, subject, authority grant, expected postconditions, and idempotency identity before the external effect is reachable. After actuation, an acknowledgement is only transport evidence. DONE requires an observation of the admitted consequence, closure of the authority bound, final receipt persistence, and enough provenance to replay verification without reacquiring actuation capability.

## Failure modes and falsifiers

The key falsifiers are receipt-after-effect ordering, missing exact subject identity, a changed post-state inheriting an old receipt, an ambiguous actuator response being blindly retried, or a receipt that verifies after any bound field is altered. A robust schema makes those failures typed. If final persistence fails after an attempt, standing is BLOCKED/AMBIGUOUS with the durable reservation as reconciliation handle—not falsely ALIVE and not automatically retried.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
