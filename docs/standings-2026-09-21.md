# Portfolio standings — 2026-09-21 (inspection-grade evidence receipt)

- Survey timestamp: 2026-09-21 ~19:33Z.
- Method: 8 parallel read-only survey agents. All git reads run with `--no-optional-locks`; no fetch, no build, no test anywhere in the survey. Every standing below is **INSPECTION-grade** unless a verifier note says otherwise.
- Fail-closed caveat: `inspection ≠ execution`. Nothing here claims ALIVE from this session except rows carrying explicit verifier evidence (see Verifier-evidence subsection). `UNKNOWN` is reported as UNKNOWN, never promoted.

## Per-repo standings

| repo | branch | HEAD | date | dirty (counts) | unpushed / ahead-behind | standing | evidence note |
|---|---|---|---|---|---|---|---|
| ~/xaas | main | 4b79f11 | 09-21 | 1 (test file, active WIP) | ahead origin/main 252 unpushed; crown branches ALL MERGED | PARTIAL_ALIVE | inspection |
| ~/ash_a2a | main | 2730c9b4 | 09-21 | 2 (CHANGELOG + mix.exs release edit in flight) | 4 unpushed; 5 unmerged local branches | PARTIAL_ALIVE | inspection; falsifier artifacts 12:33 local (see verifier evidence) |
| ~/ggen_igniter | feat/zcode-ocel-pack | dcebc42 | 09-21 | clean | no upstream; main behind 2 | ALIVE | verifier evidence: ggen receipts written 12:25 local 09-21 |
| ~/ash_surface | feat/dfcm-surface-core | 386135c | 09-17 | clean except untracked docs/jira/v26.9.19/ (5 OPEN operator-decision tickets) | 0/0 vs remote ref | PARTIAL_ALIVE | inspection; 050 BLOCKED; 31 fleet worktrees |
| ~/ggen-marketplace | main | 5646c7932 | 09-20 | 3 untracked dirs | ahead 3 / behind 4 vs origin | PARTIAL_ALIVE | inspection; 12 branches in external worktrees (pi-ocel-tap dirty 12, targets-shacl-zod dirty 15) |
| ~/ggen (Rust) | fix/ggen-v26.9.17-boundary | 5cc8808c1 | 09-17 | 1 untracked dir | n/s | PARTIAL_ALIVE | inspection; idle since 09-19 |
| ~/zoela_phx | exp/substrate-receipt-digest-reconcile | 71a5fe2 | 09-20 | clean | 3 ahead of main; no remote | UNKNOWN | inspection; erl_crash.dump 09-20 05:44 |
| ~/dfcm-autonomous | main | 9229ae0 | n/s | 1 | n/s | ALIVE | verifier evidence: guard run 5357 + RUNS.md appended 2026-09-21T19:32Z |
| ~/ferroplan | main | e90928d | 09-18 | 2 | n/s | PARTIAL_ALIVE | inspection; idle 3 days |
| ~/dev/zcode-cli | worktrees in ~/wt | (per-worktree) | 09-21 (commits today) | loop-gaps dirty 2; snapshot-hardening clean; zcode-3 clean | n/s | ALIVE | inspection; commits today in ~/wt worktrees |
| Workspace dirs (capacity-ride et al.) | — | — | 09-17 | — | — | UNKNOWN (dormant) | rider FINAL cut 09-17 18:24Z; 108 runs; 43 tickets terminal; log.ndjson 172 lines |
| ~/chatman-ecosystem | main | 7ac66d8 | 09-19 | clean (0 porcelain entries, re-verified at write time) | no remote | PARTIAL_ALIVE | inspection; dual-lineage namesake on GitHub (details below) |

## Verifier evidence (the ONLY executions known)

- `~/ggen_igniter`: ggen receipts written 12:25 local, 2026-09-21.
- `~/dfcm-autonomous`: guard run 5357 executed; RUNS.md appended 2026-09-21T19:32Z.
- `~/ash_a2a`: Chicago falsifier artifacts written 12:33 local, 2026-09-21. **WIP signal — not a green receipt.**
- `~/chatman-ecosystem`: prototype pytest 28/28 passing at merge 7ac66d8, 2026-09-19 (historical, prior session — not this session's evidence).
- prototype pytest re-run 2026-09-21: **28 passed in 0.07s, exit 0** (observed this session by the prototype-README writer, `python3.13 -m pytest prototype/tests -q`); demo.py exit 0 (4/4 properties, 3/3 refusals). Matches the historical 28/28 @7ac66d8 — no divergence. (This line resolved by the coordinator after the placeholder was written; placeholder text was UNKNOWN at write time because the sibling had not finished.)

## This repo (~/chatman-ecosystem)

- Local: main @7ac66d8 (2026-09-19), clean, no remote configured — unreachable from GitHub by construction.
- GitHub namesake: unrelated active lineage.
  - main @c59596f (09-11)
  - `errc` ahead 23 + PR #250
  - `agent/v26.9.20-verified-accomplishment-log` ahead 19 + PR #251, pushed 2026-09-21T03:43Z
  - `feat/daily-verified-accomplishment-log-20260920` ahead 5
  - ~250 PRs total
- The local repo and the GitHub namesake share a name, not a history. No push/pull relationship exists or is implied.

## Sources

- 8-agent parallel survey digest (2026-09-21 ~19:33Z), read-only (`--no-optional-locks`).
- `~/dfcm-autonomous/RUNS.md` (tail).
- capacity-ride `log.ndjson` (172 lines, FINAL 09-17).
- GitHub API (`gh api`, read-only) for the namesake repo.
- Write-time re-verification of this repo: `git --no-optional-locks log -1 main`, `status --porcelain` (0 entries), `remote -v` (empty).
