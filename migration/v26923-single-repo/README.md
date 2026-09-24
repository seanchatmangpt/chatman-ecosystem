# v26.9.22/23 single-repo migration record

This directory records how the v26.9.22/23 shadow topology was retired: about 190 git worktrees, integration copies
and a shadow clone under `~/wt/v26922`, plus a second clone `~/beam4pm_ws2`. The state went back into one canonical
checkout per repository under the operator's reversible migration protocol (2026-09-23/24). This directory is
evidence; the topology guard does not scan `migration/`.

| file | phase | what it is |
|---|---|---|
| `MANIFEST.json` (+ `.sha256`) | 1 | inventory of every shadow worktree, branch, dirty path and non-git file |
| `PRESERVE.json` | 2 | 1016 preservation refs under `refs/archive/pre-single-repo-migration/20260924T0600Z/*`, 16 dirty snapshots, the shadow-files archive commit (2650 files) and ignored evidence |
| `OWNERSHIP.json` | 3 | disposition per subject; every UNIQUE_AND_REQUIRED and release subject is bound to structured evidence `{repo, commit, path, kind}` |
| `steps.jsonl` | 8-12 | the cutover and retirement ledger (one line per actuation, with exit codes) |
| `verify/gate-final.json` | 11 | `tools/cleanup_gate.py`: every destructive-cleanup precondition held before retirement |
| `verify/restore-drill.txt` | 10 | rollback drill: `git archive` of the shadow-files archive was byte-equal to the live tree |
| `FINAL-RECEIPT.json` | 13 | stop condition recomputed from live state by `tools/final_receipt.py`: `git worktree list` of every affected repo, rollback, ownership, merges, and the recurrence guard. It validates against the fleet R schema. |
| `driver/` | CE-RECORD | the GC-26.9.23 driver log, moved out of the shadow tree |

The preservation refs are local to the canonical checkouts. After retirement, the shadow clone's refs live in
this repository under `.../shadow-clone/*`, and `beam4pm_ws2`'s refs live in beam4pm under `.../beam4pm_ws2/*`.
`tools/` holds copies of the migration scripts. They name absolute local paths of the machine that ran them
and are recorded as run, not as reusable tooling.
