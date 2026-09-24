# CE23 annex: driver scan plan (moved evidence)

`scan-plan.json` is a byte-identical copy (sha256
`29e3c1c8008926a046c71df9eaf9df59084ab4e75c20aa2ad9d17f2f4be0b7eb`, 157425 bytes, `cmp` exit 0) of
the file `v26922/v26923/lanes/scan-plan.json` in the GC-26.9.23 driver's retired shadow tree (full
source path and the shadow's status: `migration/v26923-single-repo/driver/README.md`), written
2026-09-23 15:00 PT. It is the synthesized wave plan of loop scan `wf_cf07ec8e-051` (56 of 75
candidates kept by the skeptics, grouped into 8 waves) with its `repo_map`, `operator_edges`,
`dropped` candidates and narrative `summary`. Step CE-RECORD moved it on 2026-09-24 so the CE23
record no longer depends on the shadow. It is recorded evidence (O), not a work graph: the CE23
orders are compiler output of the prose in `../` (`goal.ttl`, `compiled/`), no court or generator
reads this file, and the historical checkout paths inside it are evidence of the plan as written.

## Scan-verified implementation specs (moved 2026-09-24)

- `specs/` holds 47 files: the CE23-*, CE-*, GC23-* and GEN-* implementation specs that loop scan
  `wf_cf07ec8e-051` kept, plus `plan.final.min.json`, the synthesized plan they belong to
  (sha256 `03bf9cfc2efd572a...`).
- `successor-specs/` holds the GC24-* and GC26924-* specs, which the plan assigns to successor GC-26.9.24,
  plus the successor summary `succ.txt`.
- Each file is a byte-identical copy (`cp -p`) of `SCAN-synthesize/specs/` in the driver's scratch
  directory `/private/tmp/claude-501/v23-scratch/`. That directory is non-durable (see
  `migration/v26923-single-repo/OWNERSHIP.json`, subject "CE23 scan-verified implementation specs").
- They are recorded evidence (O). Commands inside them that name retired shadow paths or
  worktree creation describe the plan as written; they are not procedures. Example:
  `CE23-11-tag.txt` must be retargeted to a `git archive` export before CE23-11 runs.
- The bench draft qualifier and extraction helper moved to `../../bench/tools/`.
