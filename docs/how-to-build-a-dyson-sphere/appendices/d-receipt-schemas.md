# Appendix D — Receipt Schemas

This appendix is a reusable reference surface for the manuscript. It is intentionally explicit about scope and evidence: examples illustrate representation and reasoning; they do not claim that a physical Dyson system has been built, tested, or admitted.

Standing belongs to an exact subject. Inspection is not execution, execution is not verification, and a named receipt file is not evidence that the intended transition occurred. A useful receipt binds identity, authority, consequence, verifier result, and replay instructions so a later observer can reconstruct why the standing claim was made.

## Sections

- [Observation Receipt](d-01-observation-receipt.md)
- [Admission Receipt](d-02-admission-receipt.md)
- [Construction Receipt](d-03-construction-receipt.md)
- [Actuation Receipt](d-04-actuation-receipt.md)
- [Verification Receipt](d-05-verification-receipt.md)
- [Replay Receipt](d-06-replay-receipt.md)

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix D — Receipt Schemas** is not retained as a label-only reference. A receipt is the boundary between an assertion that work happened and evidence that a particular consequential transition has standing. It must bind the exact subject, admitted intent, authority, pre-state, attempted mutation, post-state observation, verifier, outcome, and replay identity. Merely naming a JSON object `receipt` is insufficient; the object has to make substitution and ambiguity mechanically detectable.

## System contract

For consequential DO, reservation precedes actuation. The reservation binds the candidate, subject, authority grant, expected postconditions, and idempotency identity before the external effect is reachable. After actuation, an acknowledgement is only transport evidence. DONE requires an observation of the admitted consequence, closure of the authority bound, final receipt persistence, and enough provenance to replay verification without reacquiring actuation capability.

## Failure modes and falsifiers

The key falsifiers are receipt-after-effect ordering, missing exact subject identity, a changed post-state inheriting an old receipt, an ambiguous actuator response being blindly retried, or a receipt that verifies after any bound field is altered. A robust schema makes those failures typed. If final persistence fails after an attempt, standing is BLOCKED/AMBIGUOUS with the durable reservation as reconciliation handle—not falsely ALIVE and not automatically retried.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
