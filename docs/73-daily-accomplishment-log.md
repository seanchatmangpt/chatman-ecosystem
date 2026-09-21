# Daily accomplishment log

The daily accomplishment log is a deterministic projection over typed evidence. It does not infer accomplishment from commit volume, PR state, workflow existence, merge state, publication, deployment, or prose claims.

## Admission rule

A unit contributes exactly one plant credit only when all of these are true:

1. `semantic_commit=true`.
2. `state=COMPLETED`.
3. `consequence_status=VERIFIED`.
4. the receipt has an identity, verifier, named consequence, and at least one evidence reference.
5. the exact `(repository, commit_sha)` has not already been credited that day.
6. the `semantic_unit_id` does not map to conflicting commit identities.

Anything failing the rule is retained under open gaps, blocked items, or unverified/not credited. The daily projection remains `PENDING_USER_REVIEW`; review cannot manufacture missing verification.

## Target calculus

The plant target is 250 unique verified semantic commits/hour. The report shows all 24 Los Angeles hour buckets, the daily-equivalent target of 6,000, daily-equivalent attainment, and the peak verified hourly rate. This avoids using raw commit counts as a proxy for verified consequence.

## Evidence input

Place `.json` or `.jsonl` records under `accomplishments/evidence/` using `schemas/accomplishment-evidence.schema.json`. The compiler scans recursively, filters by the requested America/Los_Angeles calendar day, and emits a Markdown review artifact.

```bash
python3 -m unittest tests/test_compile_accomplishment_log.py -v
python3 scripts/compile_accomplishment_log.py --date 2026-09-20 --evidence-dir accomplishments/evidence
```

The scheduled workflow runs after local midnight year-round and compiles the previous Los Angeles calendar day. It has `contents: read` only and uploads a review artifact; it does not mutate repository state, merge, publish, deploy, or promote standing.
