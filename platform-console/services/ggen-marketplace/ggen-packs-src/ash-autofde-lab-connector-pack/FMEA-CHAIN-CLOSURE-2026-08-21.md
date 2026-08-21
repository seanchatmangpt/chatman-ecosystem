# Design FMEA Chain Closure — `add_connector.py` (ash-autofde-lab-connector-pack)

Date: 2026-08-21
Scope: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/scripts/add_connector.py`

This record independently re-verifies all 5 findings from this session's Design FMEA
chain against the real, current state of the repo and its two open worktrees — not
copied from prior commit-message claims. Every command below was actually re-run
today; output is quoted from that re-run.

## Summary table

| # | Finding | RPN (S×O×D) | Fix commit | Location | Real re-run result | Merge status |
|---|---|---|---|---|---|---|
| 1 | Bridge wiring on nonexistent Ash module | 8×8×9 = **576** | `e0013236d8345b202badf944034c9cd3639e03f9` | `main` | 3/3 pass | **On main** |
| 2 | Ontology write not rolled back on `--deploy` failure | 7×4×9 = **252** | `fd1e62818f71ee777e7c5ff88cd7cd07a8f4e83c` | `main` | 2/2 pass | **On main** |
| 3 | Stale generated file silently copied on ggen no-op | 6×3×8 = **144** | `880f9dde8151da8fb9289ad2172602106d76a6b7` | `main` | 4/4 pass | **On main** |
| 4 | TOCTOU race on concurrent `add_connector.py` invocations | 7×2×9 = **126** | `ec01581b1c8be5af4a72be5a5e6e6113ebf464df` | branch `fix-rpn126-connector-toctou-race` | 14/14 pass | **NOT merged — pending** |
| 5 | Hand-edited xaas dest file silently overwritten | 8×3×9 = **216** | `525b38ad5702b99e1182b6aef8022449513105e6` | branch `fix-connector-overwrite-hand-edits` | 20/20 pass | **NOT merged — pending** |

(Finding 5 was carried into this session's task as "unranked"; the fix commit itself
computed a real RPN of 216 — recorded here as found, not left unranked.)

## Re-verification detail

### 1–3: `main` branch (RPN 576 / 252 / 144)

`main` HEAD at time of this record: `0c904ac60a699b76cd28c80fa52413cf4880ba21`
(2026-08-21 06:02:20 -0700).

Ancestry check re-run today:

```
$ git merge-base --is-ancestor e001323 HEAD && echo ancestor   # RPN=576
e001323: IS ancestor of HEAD (main)
$ git merge-base --is-ancestor fd1e628 HEAD && echo ancestor   # RPN=252
fd1e628: IS ancestor of HEAD (main)
$ git merge-base --is-ancestor 880f9dd HEAD && echo ancestor   # RPN=144
880f9dd: IS ancestor of HEAD (main)
```

All three fixes live in the same file (`scripts/add_connector.py`) with dedicated
regression test modules. Re-ran the full `scripts/` suite fresh, from a clean
`git status --short` on `add_connector.py` and its tests (no local edits):

```
$ python3 -m pytest scripts/ -v
scripts/test_add_connector_bridge_guard.py::test_backfill_refuses_and_leaves_bridge_untouched_when_module_missing PASSED
scripts/test_add_connector_bridge_guard.py::test_backfill_wires_bridge_once_module_actually_exists PASSED
scripts/test_add_connector_bridge_guard.py::test_running_backfill_twice_is_idempotent_once_module_exists PASSED
scripts/test_add_connector_deploy_rollback.py::test_real_manifest_is_untouched_by_this_test PASSED
scripts/test_add_connector_deploy_rollback.py::test_deploy_failure_after_ontology_write_rolls_back_and_permits_retry PASSED
scripts/test_add_connector_stale_copy_refusal.py::test_real_manifest_is_untouched_by_this_test PASSED
scripts/test_add_connector_stale_copy_refusal.py::test_silent_noop_sync_refuses_instead_of_copying_stale_file PASSED
scripts/test_add_connector_stale_copy_refusal.py::test_genuine_fresh_write_still_succeeds_and_copies_real_bytes PASSED
scripts/test_add_connector_stale_copy_refusal.py::test_first_ever_write_with_no_prior_file_still_succeeds PASSED
9 passed in 0.54s
```

Chicago-style check re-run:

```
$ grep -rn "unittest.mock\|Mock(\|MagicMock\|patch(\|monkeypatch" scripts/*.py
```

Only docstring lines *naming* what is absent (e.g. "No unittest.mock, Mock(), ...
anywhere in this file"); zero actual usages.

Production `ontology.ttl` confirmed untouched by any of this: `git diff --stat
ontology.ttl` → empty.

### 4: `fix-rpn126-connector-toctou-race` (RPN=126) — worktree, NOT merged

Worktree: `~/chatman-ecosystem/.claude/worktrees/fix-rpn126-connector-toctou-race`
Branch HEAD: `ec01581b1c8be5af4a72be5a5e6e6113ebf464df` (2026-08-21 05:35:50 -0700)
Based on `880f9dd` (pre-dates the two later `main` release commits, `ed3ca47` /
`0c904ac`).

```
$ git merge-base --is-ancestor HEAD main
NOT merged to main
```

Full `scripts/` suite re-run fresh inside the worktree (its own checkout of
`add_connector.py` and tests, including the new
`test_add_connector_concurrency_lock.py`):

```
$ python3 -m pytest scripts/ -v
... (9 pre-existing bridge-guard/rollback/stale-copy tests) ...
scripts/test_add_connector_concurrency_lock.py::test_real_manifest_is_untouched_by_this_test PASSED
scripts/test_add_connector_concurrency_lock.py::test_two_concurrent_appends_for_different_tools_both_survive PASSED
scripts/test_add_connector_concurrency_lock.py::test_lock_timeout_fails_loudly_instead_of_hanging_or_clobbering PASSED
scripts/test_add_connector_concurrency_lock.py::test_single_noncurrent_invocation_still_works_unchanged PASSED
scripts/test_add_connector_concurrency_lock.py::test_two_concurrent_backfill_bridge_extensions_for_different_tools_both_survive PASSED
14 passed in 6.05s
```

Mock grep re-run: zero real usages, only docstring disclaimers.

### 5: `fix-connector-overwrite-hand-edits` (RPN=216) — worktree, NOT merged

Worktree: `~/chatman-ecosystem/.claude/worktrees/fix-connector-overwrite-hand-edits`
Branch HEAD: `525b38ad5702b99e1182b6aef8022449513105e6` (2026-08-21 05:54:11 -0700)

This branch is a real merge of `fix-rpn126-connector-toctou-race` (`ec01581`) into a
branch cut from local `main` at `ed3ca47`, so it carries the RPN=126 fix plus its own
hand-edit-refusal fix on top of the merged code — confirmed by `git log --oneline -5`
showing `f23cb96 Merge branch 'fix-rpn126-connector-toctou-race' into
fix-connector-overwrite-hand-edits` directly above `ec01581`.

```
$ git merge-base --is-ancestor HEAD main
NOT MERGED (confirmed)
```

Full `scripts/` suite re-run fresh (20 tests: the 14 above plus 6 new in
`test_add_connector_hand_edit_refusal.py`):

```
$ python3 -m pytest scripts/ -v
... (14 tests as above) ...
scripts/test_add_connector_hand_edit_refusal.py::test_real_manifest_is_untouched_by_this_test PASSED
scripts/test_add_connector_hand_edit_refusal.py::test_first_ever_generation_succeeds_and_records_sidecar_hash PASSED
scripts/test_add_connector_hand_edit_refusal.py::test_clean_redeploy_succeeds_when_dest_matches_last_known_hash PASSED
scripts/test_add_connector_hand_edit_refusal.py::test_hand_edited_dest_refuses_overwrite_without_force PASSED
scripts/test_add_connector_hand_edit_refusal.py::test_hand_edited_dest_overwritten_with_force PASSED
scripts/test_add_connector_hand_edit_refusal.py::test_dest_exists_with_no_sidecar_refuses_as_unknown_provenance PASSED
20 passed in 6.84s
```

Gate check re-run:

```
$ python3 scripts/run_gates.py
PASS 010_required.rq
PASS 020_unique_output_file.rq
2 gate(s) run, 0 total violation(s)
```

Mock grep re-run: zero real usages, only docstring disclaimers.

## Pending human decision

Findings 4 (RPN=126) and 5 (RPN=216) are real, tested fixes sitting on two real,
unmerged branches — not an oversight. `main` currently ships only findings 1–3
(576 / 252 / 144 closed). The TOCTOU race (concurrent `add_connector.py` runs
clobbering each other's writes) and the hand-edit-overwrite gap (a redeploy landing
on an already-generated `xaas` file silently discarding a hand-edit) remain open on
`main` until a human reviews and merges `fix-connector-overwrite-hand-edits` (which
already contains `fix-rpn126-connector-toctou-race` merged into it) into `main`.

No other action was taken on either worktree branch as part of this closure record —
no merge, no push, no rebase. This document only records what was independently
re-verified today.
