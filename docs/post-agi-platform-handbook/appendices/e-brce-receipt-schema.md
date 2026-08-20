# Appendix E — BRCE Receipt Schema

A conceptual BRCE receipt can be represented as:

```json
{
  "receipt_id": "blake3:<digest>",
  "subject": {
    "id": "service:example",
    "revision": "<exact-revision>"
  },
  "intent": {
    "capability": "deploy",
    "artifact_digest": "blake3:<digest>"
  },
  "authority": {
    "principal": "principal:<id>",
    "policy": "policy:<version>",
    "scope": "subject-only"
  },
  "execution": {
    "adapter": "adapter:<id>",
    "started_at": "<timestamp>",
    "completed_at": "<timestamp>"
  },
  "postcondition": {
    "expected": "<typed predicate>",
    "observed": "<typed evidence>"
  },
  "parents": ["blake3:<parent-receipt>"],
  "replay": {
    "toolchain": "<identity>",
    "mode": "<mode>"
  }
}
```

This is a conceptual reference, not a replacement for the repository's canonical receipt schema.

## Verification obligations

A verifier should check structural validity, exact-subject binding, authority relationship, artifact identity, postcondition evidence, parent integrity, and any cryptographic authentication required by policy.

A hash alone does not prove authorized origin.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix E — BRCE Receipt Schema** is not retained as a label-only reference. A receipt is the boundary between an assertion that work happened and evidence that a particular consequential transition has standing. It must bind the exact subject, admitted intent, authority, pre-state, attempted mutation, post-state observation, verifier, outcome, and replay identity. Merely naming a JSON object `receipt` is insufficient; the object has to make substitution and ambiguity mechanically detectable.

## System contract

For consequential DO, reservation precedes actuation. The reservation binds the candidate, subject, authority grant, expected postconditions, and idempotency identity before the external effect is reachable. After actuation, an acknowledgement is only transport evidence. DONE requires an observation of the admitted consequence, closure of the authority bound, final receipt persistence, and enough provenance to replay verification without reacquiring actuation capability.

## Failure modes and falsifiers

The key falsifiers are receipt-after-effect ordering, missing exact subject identity, a changed post-state inheriting an old receipt, an ambiguous actuator response being blindly retried, or a receipt that verifies after any bound field is altered. A robust schema makes those failures typed. If final persistence fails after an attempt, standing is BLOCKED/AMBIGUOUS with the durable reservation as reconciliation handle—not falsely ALIVE and not automatically retried.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
