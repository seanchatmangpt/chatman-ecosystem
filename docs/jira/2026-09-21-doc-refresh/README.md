# 2026-09-21-doc-refresh

## Metadata

| field | value |
|---|---|
| id | `2026-09-21-doc-refresh` |
| created | 2026-09-21T19:53:25Z |
| type | documentation-refresh |
| standing | PARTIAL_ALIVE (docs written, uncommitted — commit is an operator cut) |
| repo base | local main @7ac66d8 (2026-09-19), full SHA `7ac66d8c55ce4aba62cd6416e9f3eecd358700e4` |
| tree state | uncommitted by design; operator review pending; NO git mutations performed by any writer |

## Goal

All docs in `~/chatman-ecosystem` updated or archived to match the current status of everything, per operator directive 2026-09-21.

## Preconditions

What prompted this session:

- The 8-agent read-only portfolio survey (2026-09-21 ~19:33Z) found this repo's docs dated 2026-09-12 while the fleet moved on — documentation drift confirmed across the portfolio.
- Dual-lineage discovery: the local repo has never been pushed; GitHub `seanchatmangpt/chatman-ecosystem` is an unrelated active lineage (main @c59596f, 2026-09-11) with open PR #250 "MuStar, governance courts, OCEL and SLA closure" and PR #251 "verified daily accomplishment log for 250/hour plant accounting" pushed 2026-09-21T03:43Z (branch `feat/daily-verified-accomplishment-log-20260920`, ahead 5, ~250 PRs total). Local SHA `7ac66d8` 404s on the remote — the two histories share a name, not a lineage.
- Consequence: docs refresh proceeds locally only; any reconciliation with the GitHub namesake is deferred to an explicit operator cut (see Remaining).

## Dispatch table

8 areas, dispatched in parallel, one writer per area, no shared files.

| # | area | owning artifact | notes |
|---|---|---|---|
| 1 | STATUS.md (index) | `/Users/sac/chatman-ecosystem/STATUS.md` | top-level index, refreshed to current state |
| 2 | census re-verification | `/Users/sac/chatman-ecosystem/census/2026-jurisdiction-census.md` | re-verify census claims against current tree |
| 3 | AGENTS.md law alignment | `/Users/sac/chatman-ecosystem/AGENTS.md` | align law text with current operator rulings |
| 4 | scm-sigma-pack README | `/Users/sac/chatman-ecosystem/packs/scm-sigma-pack/README.md` | includes a `validate_sigma.sh` run (result lands in writer's own evidence, not here) |
| 5 | prototype README | `/Users/sac/chatman-ecosystem/prototype/README.md` | includes a pytest re-run (result lands in writer's own evidence, not here) |
| 6 | ecosystem map | `/Users/sac/chatman-ecosystem/docs/ecosystem-map.md` | repo/lineage map incl. dual-lineage discovery |
| 7 | standings | `/Users/sac/chatman-ecosystem/docs/standings-2026-09-21.md` | standing ledger entry for the fleet, 2026-09-21 |
| 8 | this ticket | `/Users/sac/chatman-ecosystem/docs/jira/2026-09-21-doc-refresh/README.md` | session history (票), written by the ticket writer |

All areas: dispatched in parallel, one writer per area, no shared files.

## History (append-only)

| ts | standing | base SHA | note |
|---|---|---|---|
| ~2026-09-21T19:33Z | UNKNOWN | 7ac66d8 | 8-agent read-only portfolio survey receipt: repo docs dated 2026-09-12, fleet moved on; dual-lineage discovery (local never pushed; GitHub namesake unrelated, main @c59596f 2026-09-11, PR #250 + #251). Observation only, no executions witnessed. |
| ~2026-09-21T19:45Z | PARTIAL_ALIVE | 7ac66d8 | Doc-refresh dispatch wave: 8 areas, one writer per area, parallel, no shared files; tree to remain uncommitted for operator review. ts approximate — reconstructed at ticket write. |
| 2026-09-21T19:53:25Z | PARTIAL_ALIVE | 7ac66d8 | This ticket written (docs/jira/2026-09-21-doc-refresh/README.md). Uncommitted. |
| 2026-09-21T19:58:30Z | PARTIAL_ALIVE | 7ac66d8 | Write wave COMPLETE: all 8 areas landed (STATUS.md, census/2026-09-21-fleet-census.md + superseded pointer, AGENTS.md aligned, pack README, prototype README, ecosystem-map, standings receipt, ticket). Verifiers observed in-session: validate_sigma.sh exit 0 (SHACL Conforms, 20-class round-trip); pytest 28/28 exit 0 (7 jurisdiction-contract tests re-passed after AGENTS.md edit — table kept byte-identical). Tree uncommitted: 2 M + 5 untracked. |

## Remaining / operator cuts

- (a) Review + commit the doc changes. The tree is intentionally left uncommitted — commit is an operator cut, no writer holds authority to commit.
- (b) Decide canonical naming / reconciliation for the GitHub namesake collision. Fetch/merge/push decisions NOT performed — no authority, hot fleet (sibling WIP agents active). Local and GitHub histories are unrelated; any reconciliation needs explicit operator authority and a quiet tree.
- (c) Sibling results (validate_sigma.sh run, pytest re-run) land in their own files — read them there; this ticket documents the dispatch, not their results.
