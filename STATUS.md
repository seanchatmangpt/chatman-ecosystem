# STATUS

Top-level status index for `chatman-ecosystem`. Purpose and law live in
`AGENTS.md`; observed ecosystem-wide reconnaissance lives in
`census/2026-jurisdiction-census.md`. This file records standing, not
doctrine. All claims dated **as of 2026-09-21**. DfCM standing
vocabulary throughout (`ALIVE | PARTIAL_ALIVE | UNKNOWN | BLOCKED |
UNSUPPORTED`); facts marked **inspection** were seen by reading, never
executed.

## Repository state (2026-09-21)

**This repo has two unrelated lineages.** They are different histories
sharing a name; no common ancestor has been established.

**Local lineage** (`~/chatman-ecosystem`, inspection, HEAD witnessed
this session): `main @7ac66d8` (2026-09-19, "Merge branch
'exp/pr3-jurisdiction-refusal-contracts': PR-3 machine-enforced
jurisdiction refusal contracts"). Working tree clean. **No git remote
is configured.** Local work to date: PR-1 (jurisdiction census +
`packs/scm-sigma-pack/` Σ ontology), the Python prototype
(`prototype/`), and PR-3 (jurisdiction refusal contracts, merged
2026-09-19). **None of this work has ever been pushed anywhere.**

**GitHub lineage** (`github.com/seanchatmangpt/chatman-ecosystem`;
branch heads witnessed this session via `git ls-remote`, counts from
the 2026-09-21 ~19:33Z survey, inspection): `main @c59596f`
(2026-09-11) — a ggen Rust workspace with `praxis-graphlaw` SHACL, an
entirely different tree. Branches: `errc/production-innovations-20260912`
ahead 23, open PR #250; `feat/daily-verified-accomplishment-log-20260920`
ahead 5, pushed 2026-09-21T03:36Z; `agent/v26.9.20-verified-accomplishment-log`
ahead 19, open PR #251, pushed 03:43Z. Roughly 250 PRs on the remote.
The local SHA `7ac66d8` appears nowhere on the remote.

**Stated plainly:** local work has never been pushed; the remote is not
behind-and-needing-a-push, it is a separate history. Reconciliation of
the two lineages is an operator cut and has **not** been performed. No
agent in the 2026-09-21 pass performed it, and this file does not
authorize one.

## Portfolio standing (2026-09-21)

All rows except "this repo" are from the 8-agent read-only survey of
2026-09-21 ~19:33Z — **inspection-only**; nothing in the table was
executed by this pass. Where the survey itself witnessed a run, that is
noted; otherwise build/test standing is UNKNOWN by DfCM rules.

| Repo | HEAD | Standing | One line |
|---|---|---|---|
| `~/xaas` | `main @4b79f11` (09-21) | PARTIAL_ALIVE | Crown v1+v2 KNOWN_REPLAY `sha256:9471200b…`, OCEL sweep 15/15; all crown branches merged; 252 commits unpushed; 1 dirty test file = active WIP |
| `~/ash_a2a` | `main @2730c9b4` (09-21) | PARTIAL_ALIVE | v26.9.18–v26.9.20 releases merged; 4 unpushed; 2 dirty files = mid-flight release edit; Chicago falsifier artifacts 12:33 local; 5 unmerged local branches |
| `~/ggen_igniter` | `feat/zcode-ocel-pack @dcebc42` (09-21) | PARTIAL_ALIVE | Clean branch; calver pack folded + 6 merges; receipts 12:25 local |
| `~/ash_surface` | `feat/dfcm-surface-core @386135c` (09-17) | BLOCKED (in part) | Quiet; 0/0 vs remote ref; 5 OPEN v26.9.19 operator-decision tickets; ticket 050 BLOCKED on pack admission; 31 fleet worktrees |
| `~/ggen-marketplace` | `main @5646c7932` (09-20) | PARTIAL_ALIVE | 319 packs; sa2a-bridge-pack v26.9.20; diverged vs origin (ahead 3 / behind 4); live WIP in `~/wt` worktrees (pi-ocel-tap dirty 12, targets-shacl-zod dirty 15) |
| `~/ggen` (Rust) | `fix/ggen-v26.9.17-boundary @5cc8808c1` (09-17) | UNKNOWN | Idle since 09-19; no build/test evidence this pass |
| `~/zoela_phx` | `exp/substrate-receipt-digest-reconcile @71a5fe2` (09-20) | UNKNOWN (build) | Clean, 3 ahead of main, no remote; `erl_crash.dump` dated 09-20 |
| `~/dfcm-autonomous` | `main @9229ae0` | ALIVE (survey-witnessed) | make-right guard run 5357 today |
| `~/ferroplan` | `main @e90928d` (09-18) | UNKNOWN | Idle 3 days, 2 dirty files |
| `~/dev/zcode-cli` | worktree-based, commits today | PARTIAL_ALIVE | Commits today via `~/wt` worktrees: loop-gaps dirty 2, snapshot-hardening, zcode-3 gall/dfcm-006 |
| `~/chatman-ecosystem` (this repo) | `main @7ac66d8` (09-19) | ALIVE (PR-1 scope only) | See below — verifier executed this session, exit 0 |
| `~/` workspace dirs | — | dormant | vision-map, gap-scan, capacity-ride, swarm-reports dormant since 09-17; ticket rider STOPPED by operator cut 09-17 18:24Z (108 runs, 43 tickets terminal); APS clone clean `@5c31d9d` |

### Standing of this repo, and its exact bound

`scripts/validate_sigma.sh` was **executed in the 2026-09-22 landing
session**, exit 0, all four gates passing: both Turtle files parse,
`ontology.ttl` conforms to `shapes.ttl` (SHACL), the generator is
byte-deterministic across two runs, and 23 classes round-trip exactly
between ontology and generated schema (the 2026-09-21 refresh added
Candidate, Admission and Replay, covering the SA2A calculus end to
end). Per
`AGENTS.md`, ALIVE is claimed for **nothing beyond** those checks.
PR-2 (composition-operator laws), PR-4 (projection-equivalence
fixture), PR-5 (runtime conservation verifier) do not exist yet and are
UNKNOWN/UNSUPPORTED. The dual-lineage split above is unresolved and is
not a passing or failing check — it is an open operator decision.

## Pointers

Sibling agents are authoring several of these today
(2026-09-21 doc-refresh pass); a pointer to a file that does not exist
yet at write time is expected, not an error. Do not treat absence as a
broken link — re-check after the pass lands.

- `census/2026-jurisdiction-census.md` — PR-1 reconnaissance across 14
  repos; observed jurisdiction violations (INFERRED, not mechanically
  enforced).
- `packs/scm-sigma-pack/README.md` — the canonical Σ ontology pack
  (PR-1 scope). [sibling-authored today]
- `prototype/README.md` — the Python prototype: verifier/compound
  porting real cross-repo patterns (praxis-graphlaw, mfw).
  [sibling-authored today]
- `docs/ecosystem-map.md` — cross-repo map. [sibling-authored today]
- `docs/standings-2026-09-21.md` — full standings detail behind the
  table above. [sibling-authored today]
- `docs/jira/2026-09-21-doc-refresh/` — tickets for this doc-refresh
  pass. [sibling-authored today]

## What this file does NOT establish

Nothing here is a runtime verification of any repo other than this
one's PR-1 validator. The portfolio table is a snapshot of one
read-only survey at ~19:33Z on 2026-09-21; dirty files and unpushed
counts move as sibling WIP agents work. No reconciliation, push, merge,
or admission decision was performed or authorized by this file. Git
state in every repo except this one is owned by its own agents; this
pass wrote exactly one file, `STATUS.md`.
