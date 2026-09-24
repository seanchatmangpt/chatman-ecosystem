# ~/wt/v26922 cleanup — 2026-09-23 13:00–13:42 PT (workflow wf_301c29f7-ec0)

Receipt: `RECEIPT.json` (validate_receipt.py ADMITTED; replay = verify_cleanup.py 363/363 + anti-vacuity). Written by the driver from the workflow output (the subagent's own write was refused).

## Result

/Users/sac/wt/v26922 went from 117G to 86G (du). `du -sh` read 117G at 13:00:28 PDT, before the workflow, and 86G (90542640 KiB) at 13:38-13:40; v23 grew by 1G meanwhile because R1a is still building. Free space on / (`df -h`) went from 49Gi (13:00) and 43Gi (13:26, just before execution) to 77Gi at 13:38. At 13:42 it read 75Gi because R1a builds are still writing. The 3 local Time Machine snapshots were thinned at 13:32 and none remain. Deleting files showed 0.00 B change on the volume until that thinning. The thinning covers the whole volume and other processes were writing at the same time, so not all of the volume gain can be credited to this cleanup. Measured per item: osx-clnr freed 8,496,324,608 bytes (7.91 GiB) from 17 ignored build/cache dirs, and the 23 repos-group worktree removals freed 5.38 GiB (5,643,152 KiB). The other 26 worktree removals were not measured at deletion; their inventory du is about 19.3G, which APFS clones may inflate.

Worktrees removed: 49; preserve refs created: 13.

## Artifacts reclaimed (osx-clnr)

7.91 GiB (8,496,324,608 bytes) from 17 ignored build/cache dirs, in 9 osx-clnr plan/approve/execute runs with 0 failures. The worktrees themselves were kept. All 10 osx-clnr R receipts, including the snapshot thin, pass the validator.
- ggen/int examples: praxis-core-verify/target 3.83GB, receiptctl/target 847MB, star-toml-verify/target 241MB, cargo-cicd-verify/target 20MB.
- autofde-lab/wo02: .venv, build and two caches, 1.46GB.
- gymact/int: .venv and caches, 251MB.
- ash_a2a/int: two native targets, 1.04GB.
- ash_atlassian/int: _build and deps, 120MB.
- ggen_igniter/int: _build and native target, 695MB. It ran without --deps, so int/deps stays; the wo-02 and wo-09 symlinks point at it.
- APFS local snapshots: 3 thinned.

## Summary

Yes, parts of ~/wt/v26922 are in use: the R1a repair lanes v23/R1-*, the REL-A scratch v23/rel-*, the frozen fri/*-int subjects and the active ZCode lanes wos/ggen-wo3/6/7. Those were not touched.

The cleanup ran in 4 steps: inventory, skeptic re-check, execute, receipt. The tree went from 117G to 86G, and free space on / went from 43Gi just before execution to 77Gi, after thinning 3 APFS snapshots that were still holding freed blocks.

**Per group** (inventoried / removed; preserve refs; osx-clnr runs):

| group | inventoried | worktrees removed | preserve refs | osx-clnr runs |
|---|---|---|---|---|
| v23 | 24 | 3 | 0 | 0 |
| wos | 5 | 1 | 0 | 0 |
| ggen-mp | 9 | 4 | 0 | 4 (+1 snapshot thin; 2 refused by the oclnr recency guard) |
| autofde-etc | 32 | 18 | 0 | 2 |
| repos | 54 | 23 | 13 | 3 |
| **total** | 124 | 49 | 13 | 9 |

Of the 124 inventoried items, 16 were ACTIVE, 49 KEEP, 38 REMOVABLE, 14 PRESERVE_THEN_REMOVE and 7 ARTIFACTS_ONLY. The skeptics approved 55 and rejected 3 (mp-wo2-ci-debt, autofde-lab/wo05-170, autofde-lab/wo10). They also dropped 1 candidate, ggen_igniter/wo-02, without a verdict.

**What was kept and preserved:**
- No branch or ref was deleted and no main checkout was touched. Every removed HEAD is still reachable from a ref, which the verifier re-checks.
- The 13 preserve refs are under refs/preserve/v26.9.23/cleanup/: 8 in xaas (fri-FRI-T3/T4/T5, law-XAAS-26922-21/26, uc-rt-A/B, uc-watch) and 5 in ggen_igniter (law-15-A/15-B/18-A/18-B, wo-03).
- Coverage was proven before each removal, and none of the snapshots contains a signing.key.
- 4 gymact uv.lock files were copied into the cleanup dir, and their hashes were verified.

**Deleted without a copy, by an approved decision:**
- 4 per-checkout signing.key files, in xaas law-XAAS-26922-26, uc-rt-A, uc-rt-B and uc-watch. The ggen-mp skeptic blocked the same kind of key in mp-wo2-ci-debt, so the two groups applied different policies. Pick one.
- The ignored build and cache dirs of each removed worktree.

**Verification:** `verify_cleanup.py` passes 363/363 checks with exit 0, and fails on a corrupted manifest (anti-vacuity). All 10 osx-clnr R receipts and RECEIPT.json pass `validate_receipt.py`. Freed space for 26 of the worktree removals was not measured per item.

**SUMMARY.md was not written:** the harness blocked the report-file write, so the operator summary is in this output (left_for_operator) instead.

**Biggest reclaim available next:**
- wos/ggen-wo7 target: 5.9G, eligible now through oclnr.
- The merged v23 lanes: about 16.8G, eligible between 14:21 and 23:32 PDT.
- fri/FRI-T2: 2.0G after 13:48.
- frozen-duckdb/int target: 2.1G after 14:52.

## Left for the operator

- mp-wo2-ci-debt (2.7G): holds 2 private signing.key files and .ggen-v2 receipts that exist nowhere else. Either copy the keys (mode 600) to cleanup/keys/ and verify the hashes, or accept losing them. Then snapshot with add -f of .ggen-v2 and the verifying keys, and run remove --force.
- Signing-key policy is inconsistent between groups. The repos group deleted 4 per-checkout signing.key files with their worktrees (xaas law-XAAS-26922-26, uc-rt-A, uc-rt-B, uc-watch); their verifying.key files are in the preserve commits. The ggen-mp group blocked the same kind of key. Choose one policy.
- autofde-lab/wo05-170 and autofde-lab/wo10 (about 620M each plus 423M of submodule clones): clean, HEAD on master. Removal needs --force because 8 submodule clones are initialized, and the rule does not allow that. Decide whether to extend --force to verified-clean submodule clones.
- autofde-lab/pr163 (579M): a one-line uncommitted change whose blob is in no ref, in the active ZCode L4 lane. PRESERVE_THEN_REMOVE once L4 releases it.
- gymact/w0-baseline-e75344d (27M): dirty W0 observation (3 OCEL fixtures and 5 .inspect_logs). PRESERVE_THEN_REMOVE on confirmation.
- ggen_igniter/wo-02: inventoried as ARTIFACTS_ONLY (about 663M), but the skeptic gave it no verdict. It needs a fresh verify before reclaim. ggen_igniter/wo-09 (38M) is a dirty ZCode lane.
- ggen-marketplace/int (2.7G), xaas/int and the other <repo>/int v26.9.22 merge targets: keep unless the operator retires the v26.9.22 int worktrees.
- fri/ggen_igniter-int (frozen release subject) shows ?? .oclnr-cache/ from an earlier oclnr run; ggen/int/.oclnr-cache also exists. The skeptic's note says it predates this execution. Not touched here.
- Recency-gated, time-sensitive: wos/ggen-wo7 target (5.9G) can be reclaimed through oclnr ARTIFACTS_ONLY now (worktree itself after about 22:05). fri/FRI-T2 (2.0G) after 13:48 via PRESERVE_THEN_REMOVE. frozen-duckdb/int target (2.1G), beam4pm/int (492M) and ash_surface/int (113M) after 14:52. autofde-lab/int (1.4G) after 15:12. The ggen/int rmcp-verify and ggen-cli-verify targets (524M) after about 16:41. fri/FRI-T6 (871M) after 16:47.
- Recency-gated merged v23 lanes, about 16.8G in total, eligible 14:21-23:32 PDT: V23-D-gi 14:21, V23-C 14:36, V23-D 18:13, V23-R 18:58, V23-B 19:00, V23-M 20:44, V23-L 21:04, V23-K 21:31, V23-H 22:23, V23-S 23:32. V23-H and V23-S are not on origin yet, so push friday/gc-fri-0800 first. wos/ggen-wo3 (6.6G) after about 18:16 (with --force, ignored target only). wos/ggen-wo5 (640M) after about 22:05.
- rela-gi-fmt-probe (675M) and rela-xaas-digest-probe (1.9G): R1a cites their branches. Reconsider after R1a merges and after 2026-09-24 00:07 / 00:16.
- Empty dirs wo05/ and zcode-cli/wo5/ need rmdir, which is outside the allowed actions. ferroplan/w0-venv (53M) is the toolchain for the W0 replay and was kept.
- Never-touch and active, not for decision now: the R1a lanes v23/R1-* (6), v23/rel-* (2), fri/xaas-int, fri/ggen_igniter-int, wos/ggen-wo6 (active, 26 untracked files), v23/V23-W (successor GC-26.9.24), v26923/, the top-level files and the W0 observation files.
