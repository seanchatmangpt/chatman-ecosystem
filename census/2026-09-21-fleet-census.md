# 2026-09-21 Fleet Census (re-verification of the 2026-09-12 jurisdiction census)

As of 2026-09-21. Supersedes [2026-jurisdiction-census.md](2026-jurisdiction-census.md)
(PR-1 RECONSTRUCT, 2026-09-12), which is preserved unmodified except for a
SUPERSEDED-BY pointer.

Evidence honesty: the authoritative input is the 8-agent read-only fleet survey
of 2026-09-21 (~19:33Z), which is **inspection-only** — no fetches, no builds,
no test runs, no execution receipts. Rows below are marked accordingly:
OBSERVED = seen in-session by this census; DIGEST = from the 09-21 survey
(inspection-only); 09-12 = carried over from the old census, **not re-verified
since 2026-09-12**, inspection-only. Standing vocabulary is the DfCM set
(`ALIVE | PARTIAL_ALIVE | UNKNOWN | BLOCKED`); here `ALIVE` means "the survey
observed fresh receipt/telemetry artifacts dated today", never this-census
execution.

## 1. This repo's own census context (chatman-ecosystem)

- Local `main` @ `7ac66d8` (2026-09-19, "Merge branch
  'exp/pr3-jurisdiction-refusal-contracts'") **never pushed** — OBSERVED, and
  structural: the repo has **no git remote configured at all** (`git remote -v`
  is empty). PR-3 exists only on this machine.
- The GitHub **namesake is an unrelated active lineage**: `main` @ `c59596f`
  (2026-09-11), with open PRs #250/#251 pushed 2026-09-21T03:43Z — DIGEST,
  inspection-only (not fetched this pass). Any GitHub-side review or merge
  against that repo does not see this lineage.
- Untracked file present: `packs/scm-sigma-pack/README.md` — OBSERVED.
- Discrepancy flag carried from the old artifact: the 09-12 census header
  claims "14 named repos" but its table contains **12 rows**; the two missing
  names were never identified. This census keeps all 12 carryover rows and adds
  the 11 fleet surfaces the survey actually covered.

## 2. Active fleet (2026-09-21 DIGEST, inspection-only)

| Repo / surface | Branch @ SHA (date) | Standing | Sync / push state | Notes |
|---|---|---|---|---|
| **~/xaas** | `main` @ `4b79f11` (09-21) | ALIVE (digest: Crown v1+v2 KNOWN_REPLAY, OCEL 15/15) | ahead of origin 252 unpushed; 1 dirty test file | Crown branches ALL MERGED; dirty file = active WIP |
| **~/ash_a2a** | `main` @ `2730c9b4` (09-21) | PARTIAL_ALIVE (digest: mid-flight release edit) | 4 unpushed; 2 dirty; 5 unmerged local branches | v26.9.18–v26.9.20 releases merged; Chicago falsifier artifacts 12:33 today (active WIP) |
| **~/ggen_igniter** | `feat/zcode-ocel-pack` @ `dcebc42` (09-21) | ALIVE (digest: receipts 12:25 local, clean) | calver pack folded + 6 merges | clean per digest |
| **~/ash_surface** | `feat/dfcm-surface-core` @ `386135c` (09-17) | BLOCKED (digest: 050 blocked on pack admission) | quiet | 5 OPEN v26.9.19 operator-decision tickets; 31 fleet worktrees |
| **~/ggen-marketplace** | `main` @ `5646c7932` (09-20) | ALIVE (digest) | **diverged vs origin: ahead 3 / behind 4** | 319 packs (was 300 on 09-12); sa2a-bridge-pack v26.9.20; WIP in `~/wt` (pi-ocel-tap 12, targets-shacl-zod 15) |
| **~/ggen** (Rust) | `fix/ggen-v26.9.17-boundary` @ `5cc8808c1` (09-17) | UNKNOWN (idle since 09-19; idle ≠ dead) | not stated by digest | 09-12 census row carried; verification path was already UNSUPPORTED then |
| **~/zoela_phx** | `exp/substrate-receipt-digest-reconcile` @ `71a5fe2` (09-20) | UNKNOWN (build UNKNOWN: `erl_crash.dump` present) | clean, 3 ahead of local main, **no remote** | 産面 consumer repo |
| **~/dfcm-autonomous** | `main` @ `9229ae0` | ALIVE (digest: guard run 5357 today) | not stated by digest | absent from 09-12 census — added here |
| **~/ferroplan** | `main` @ `e90928d` (09-18) | UNKNOWN (idle 3 days) | 2 dirty | absent from 09-12 census — added here |
| **~/dev/zcode-cli** | commits today via `~/wt` | ALIVE (digest: fresh work) | loop-gaps dirty 2; snapshot-hardening; zcode-3 | absent from 09-12 census — added here |
| **Workspace subsidiaries** (vision-map, gap-scan, capacity-ride, swarm-reports, capacity-probe) | n/a | dormant since 09-17 | rider STOPPED 2026-09-17 18:24Z (108 runs, 43 tickets terminal) | APS clean @ `5c31d9d` |

## 3. Carryover rows from the 09-12 census (jurisdiction claims, NOT re-verified since 2026-09-12)

Standing as of 09-21 is **UNKNOWN** for all rows below; the 09-12 survey did
not cover them and no fetch/build was run since. Jurisdiction findings are
repeated verbatim-in-substance from the old census and remain INFERRED,
inspection-only.

| Repo | Jurisdiction summary (09-12, inspection-only) | 09-12 violation flag (unchanged, INFERRED) |
|---|---|---|
| **ggen-ecosystem** | canonical composition root; SELECT/CONSTRUCT/DO separation; receipted-broker-only DO | none found on 09-12 |
| **beam4pm** | BEAM process-mining substrate, app code ggen-manufactured | planner+actuator+auditor fused (first-party actuation + own receipt chain) |
| **ash_r2rml** | hooks manufacture intents, never actuate | none found on 09-12 — closest to clean single jurisdiction |
| **mfw** | Monorepo Agent Law governing admission/receipt/replay/actuation boundaries | two differently-scoped `runtime/` dirs (naming smell, unconfirmed) |
| **bcinr** | deterministic substrate constitution; planner+actuator+auditor bundled | BY-DESIGN (ADMITTED umbrella scope), not a violation |
| **gymact** | lawful executable-world layer for AutoFDE | Rust/Python internal duplication of authority/receipt/runtime |
| **ash_pplan** | semantic/control-plane projection, not a fourth workflow engine | none found on 09-12 — cleanest observed match |
| **autofde-lab** | "computes candidate plans, does not actuate" | CONFIRMED-strongest on 09-12: `openclaw_runtime.py` + duplicated `gymact/` ontology namespace against its own doctrine |

`chatman-ecosystem`, `ggen`, `ggen-marketplace` and `ash_a2a` also appear in
Section 2 with current standing; their 09-12 jurisdiction analysis carries over
under the same inspection-only caveat.

## 4. Status flips vs the 2026-09-12 census

1. **ggen-marketplace**: 300 pack dirs → **319 packs** (+ sa2a-bridge-pack
   v26.9.20); sync state unknown-then → **diverged vs origin (ahead 3/behind
   4)**; first observed cross-repo WIP footprint (`~/wt` worktrees).
2. **ash_a2a**: quiet dispatch-layer repo with a static violation flag → now
   the hottest surface (three releases merged, falsifier artifacts dated
   today, mid-flight release edit). The 09-12 co-location violation
   (dispatcher owning `planning.ex` + `execute_command.ex`) is neither
   re-verified nor cleared.
3. **ggen (Rust)**: was UNSUPPORTED-verification → now idle 2+ days on a
   boundary-fix branch; standing UNKNOWN.
4. **chatman-ecosystem**: "created fresh by PR-1" → now carries a locally
   merged PR-3 (jurisdiction refusal contracts) at `7ac66d8`, never pushed;
   plus an untracked `packs/scm-sigma-pack/README.md`.
5. **Fleet shape**: the live frontier has moved to xaas / ash_a2a /
   ggen_igniter / ash_surface / ggen-marketplace / dfcm-autonomous /
   dev/zcode-cli — seven surfaces the 09-12 census did not name; the eight
   repos it did name (beyond the four above) dropped out of survey scope and
   are UNKNOWN as of 09-21.

## 5. What this re-verification does NOT establish

No fetch, no builds, no test runs, no execution against any subject: every
standing value above is file/metadata observation (inspection-only), not a
receipt. `ALIVE` rows rest on the survey agents' observation of artifacts
dated 2026-09-21, not on this census executing anything. The 09-12 INFERRED
jurisdiction violations remain unmechanically-enforced hypotheses; PR-3's
refusal contracts were not exercised this pass, and nothing here advances
them from INFERRED to VERIFIED. A mechanical jurisdiction audit remains
future work.
