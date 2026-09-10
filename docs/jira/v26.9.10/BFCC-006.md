# BFCC-006 — BFCC CI Conformance Workflow

Ticket Key: BFCC-006
Owning repo: seanchatmangpt/chatman-ecosystem
Exact base ref/SHA: main @ 83204ee38a518311d9c9fc128d69c517a99257f4
Standing: BFCC-CANDIDATE
Depends on: BFCC-003, BFCC-004

## Problem

Without CI enforcement, `catalog/bfcc.toml`, `scripts/verify_bfcc.py`, and
`scripts/bfcc_benchmark.py` can drift out of sync with each other or regress silently
on a future PR — exactly the exact-head CI discipline every other conformance profile
in this repo (`formation-profile.yml`, `dfcm-autonomic-finish.yml`) already enforces
for itself.

## Customer/system need

Any PR touching BFCC's manifest, ontology, or scripts needs an automatic, real
verification run against the exact PR head SHA before merge — not a manual, easy-to-
forget step.

## Scope

`.github/workflows/bfcc-conformance.yml`, mirroring `formation-profile.yml`'s shape:

- `on.pull_request.paths`: exactly `catalog/bfcc.toml`, `ontology/bfcc.ttl`,
  `ontology/bfcc.shacl.ttl`, `scripts/verify_bfcc.py`, `scripts/bfcc_benchmark.py`,
  `tests/test_bfcc.py`, `tests/test_bfcc_benchmark.py`, and the workflow file itself.
  Plus `workflow_dispatch`.
- `permissions: contents: read` (minimal, matching the sibling workflows).
- `env.CANDIDATE_SHA = ${{ github.event.pull_request.head.sha || github.sha }}`.
- Steps: checkout at `CANDIDATE_SHA` with pinned-SHA `actions/checkout`
  (`persist-credentials: false`); assert `git rev-parse HEAD == CANDIDATE_SHA`; pinned-
  SHA `actions/setup-python` (3.12); `python3 -m unittest -v tests.test_bfcc
  tests.test_bfcc_benchmark`; `python3 scripts/verify_bfcc.py --root . --json | tee
  bfcc-receipt.json`; upload `bfcc-receipt.json` as a build artifact
  (`if: always()`, `if-no-files-found: warn`).
- `timeout-minutes: 5`.

## Non-goals

- No automatic merge-blocking beyond what GitHub's own required-checks configuration
  already provides repo-wide — this ticket only adds the check, not branch-protection
  policy changes.
- No deployment/release action of any kind — pure verification.

## Dependencies

BFCC-003 and BFCC-004 (the scripts/tests this workflow invokes must exist first).

## Risks

Action SHAs must be pinned to the same commit SHAs already used elsewhere in this
repo's workflows (`actions/checkout`, `actions/setup-python`, `actions/upload-
artifact`) rather than re-resolved from tag names, to avoid supply-chain drift between
workflows.

## Authority boundary

CI verification only — `contents: read`, no write/deploy permission requested.

## Rollback

Delete the workflow file; no other workflow depends on it.

## Acceptance commands

```
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/bfcc-conformance.yml')); print('YAML OK')"
gh workflow list | grep -i bfcc
```

## Observable Definition of Done

- Workflow file is valid YAML, triggers only on the exact paths listed above plus
  `workflow_dispatch`.
- A real PR touching any BFCC file triggers the workflow and it completes, uploading
  a real `bfcc-receipt.json` artifact.
- Action versions are pinned by commit SHA with a version comment, matching this
  repo's existing convention.
