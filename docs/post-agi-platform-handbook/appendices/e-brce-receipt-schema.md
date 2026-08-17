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