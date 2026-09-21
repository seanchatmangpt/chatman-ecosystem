# Accomplishment evidence ingress

Daily accomplishment reports consume JSONL records from `evidence/accomplishments/*.jsonl`. This directory is an evidence ingress, not a standing authority. Records conform to `schemas/accomplishment-evidence.schema.json` and carry `schema=chatman.accomplishment-evidence/1`.

A record is countable toward the **250 verified unique semantic commits/hour** plant target only when all of these bind to one exact Git subject:

- `semantic_fingerprint`: 64 lowercase hex characters identifying the semantic unit;
- `repository`: exact `owner/repo`;
- `source_sha`: exact 40-character commit SHA;
- `completed_at`: timezone-aware completion timestamp;
- `state`: `COMPLETED`;
- `consequence.identity`: non-empty verified consequence identity;
- `consequence.verified`: `true`;
- `verification.verifier`: non-empty repository-native verifier identity;
- `verification.outcome`: `PASS`;
- `verification.receipt_id`: non-empty receipt identity;
- `verification.receipt_digest`: 64 lowercase hex characters.

Example:

```json
{"schema":"chatman.accomplishment-evidence/1","semantic_fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","repository":"seanchatmangpt/example","source_sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","completed_at":"2026-09-20T17:15:00-07:00","summary":"semantic admission edge","state":"COMPLETED","consequence":{"identity":"test:admission-edge","verified":true},"verification":{"verifier":"repo-native:test","outcome":"PASS","receipt_id":"receipt:example","receipt_digest":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},"blocker":""}
```

`OPEN_GAP` and `BLOCKED` records are retained in the daily report but never enter the numerator. A `COMPLETED` record missing any required consequence or receipt evidence is automatically moved into **Open gaps** and marked `UNVERIFIED` in the projection.

The compiler also fails closed when one semantic fingerprint names conflicting subjects/consequences or when multiple distinct semantic fingerprints claim the same Git subject. This prevents duplicate accounting and semantic-unit splitting from inflating plant throughput.

Generated daily logs remain `CANDIDATE` with `PENDING_USER_REVIEW`; compilation does not imply merge, publication, deployment, runtime standing, or cross-repository `ALIVE`.
