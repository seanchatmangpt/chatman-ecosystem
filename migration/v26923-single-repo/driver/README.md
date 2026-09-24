# v26.9.23 overnight driver record (moved evidence)

`DRIVER.md` is a byte-identical copy (sha256
`6f1b79395ab12a371192415419c26e1d46ef0283ea8d679f00697cb3d8c8c6b6`, 22409 bytes, `cmp` exit 0) of
`/Users/sac/wt/v26922/v26923/DRIVER.md`, last written 2026-09-23 22:47 PT by the GC-26.9.23 driver
(Claude session 1fecd79a) in the shadow tree, which was never a git repository and is retired
read-only evidence scheduled for deletion. Step CE-RECORD moved it here on 2026-09-24 under the
operator's single-repository directive (2026-09-23/24: one canonical checkout per repository,
normal git branches, no worktrees), so the record survives the shadow. The historical paths inside
it (the fri/ and v23/ lane worktrees, the `mkdir` merge locks, `lanes/`, `ticks/`, the handoff
registry) are evidence of how the driver ran, not live instructions: nothing in this repository reads
this file, and the topology guard (`scripts/topology_guard.py`, `tests/test_topology_guard.py`)
treats `migration/` as recorded evidence. The loop-scan wave plan the driver produced,
`/Users/sac/wt/v26922/v26923/lanes/scan-plan.json`, moved alongside it to
`release/v26.9.23/sjira/annex/scan-plan.json`.
