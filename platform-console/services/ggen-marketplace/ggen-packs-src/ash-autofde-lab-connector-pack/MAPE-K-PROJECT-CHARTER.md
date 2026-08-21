# Project Charter — MAPE-K/Ash/autofde-lab/ggen-marketplace/clap-noun-verb Autonomic System

**DMEDI Phase:** Define
**Charter owner:** xpointsh@gmail.com
**Date:** 2026-08-21
**Central document location:** `ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack` — this pack is the real, generated connector between the four repos in scope (its `ontology.ttl` defines the `aac:AshConnector` individuals that wire an Ash resource to a `clap-noun-verb-deploy`-served autofde-lab solver tool), and is therefore the natural cross-repo home for this charter.

---

## 1. Problem Statement

Four repositories implement the parts of a MAPE-K (Monitor–Analyze–Plan–Execute over a shared Knowledge base) autonomic loop, but the loop's real, measured closure is partial and unevenly distributed:

- **Knowledge (K) coverage is low.** Of 75 real Postgres-backed Ash resources in `~/xaas` (the MAPE-K/Ash repo), only 5 have ever been populated with at least one real persisted row (6.7% coverage). 61 resources have zero rows, and 9 resources errored outright when `mix xaas.capability_coverage` tried to count them.
- **The Monitor→Analyze trigger degrades to a stale-data path by design.** `autofde-lab`'s `phase_h_trigger.run_once()`, on its most recent real run, reported `triggered: false` (ontology hash unchanged from baseline, so no drift-triggered solve) and `coverage_gap.invoked: false` with `detection_status: "stale_skip_using_prior_observation"` — it is 2 of 5 allowed consecutive ticks into skipping a fresh coverage-gap probe and is reusing a prior observation instead of re-measuring.
- **The connector between Ash (Plan/Execute) and autofde-lab (Analyze/solver) is a single generated pack**, not yet proven at scale: its ontology declares 13 `aac:AshConnector` individuals, each wiring one Ash resource action to one `clap-noun-verb-deploy` HTTP tool call against autofde-lab's fabric CLI.
- **clap-noun-verb** (the CLI/HTTP transport layer connecting Ash to autofde-lab's solvers) is under heavy, concurrent, uninstrumented-for-this-loop churn: 43 commits in the last 6 hours across the workspace, versus 14 in `~/xaas`'s MAPE-K files and 7 in autofde-lab's three fabric-loop files in the same window — a roughly 3–6x higher change rate in the transport layer than in the loop logic it carries.

No number above is a target failure — all currently-running test suites pass at 0 failures. The problem is that the loop's *closure* (K populated, Analyze re-probing on a live signal rather than a stale skip, connector coverage matching Ash's real resource surface) is not yet established as a steady-state, measured property of the system.

## 2. Goal Statement

Establish, with real measured evidence (not narrated capability), a MAPE-K loop across `~/xaas` (Ash), `~/autofde-lab`, `ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack`, and `~/clap-noun-verb` in which:

- All four repos' real test suites continue to pass at 0 failures (current baseline, all four: 0 failures) as further Ash connector resources, autofde-lab solver bindings, and clap-noun-verb transport routes are added.
- The `mix xaas.capability_coverage` real-row coverage percentage is measured on a recurring, defined cadence (not ad hoc) so that a movement away from the 6.7% baseline is a detected fact, not an assumption. A numeric coverage *target* is explicitly deferred to the Measure/Analyze phases of this DMEDI project — no target percentage is asserted here.
- `phase_h_trigger.run_once()`'s coverage-gap probe cadence (currently: forced re-probe after `max_consecutive_skips_before_probe=5` consecutive stale skips) is reviewed against real drift/gap data collected over more than one tick, so that "stale-skip" behavior is a deliberately tuned parameter, not an unexamined default.
- The `ash-autofde-lab-connector-pack` ontology's connector count (currently 13 `aac:AshConnector` individuals) is tracked against `~/xaas`'s real resource count (75) as a named, measured ratio, without inventing an intermediate target.

## 3. Scope / Boundaries

**In scope:**
- Real code, test, and verification work on the autonomic loop itself: Ash resources and mix tasks under `~/xaas/lib/xaas/operations` and `~/xaas/lib/mix/tasks`; autofde-lab's `src/autofde_lab/fabric/phase_h_trigger.py`, `solve_and_falsify.py`, and `src/autofde_lab/receipts/broker.py`; the `ash-autofde-lab-connector-pack` ontology, templates, and generation scripts; and `clap-noun-verb`'s workspace crates (including `clap-noun-verb-macros`) that carry the HTTP transport between Ash and autofde-lab.
- Measurement, instrumentation, and closing of real gaps in the loop (e.g., the 61 zero-row Ash resources, the 9 count-errored resources, the stale-skip coverage-gap probe) using real, currently-running suites and tasks as evidence.

**Explicitly out of scope (standing instruction):**
- **No release engineering.**
- **No version bumps.**
- **No changelog work.**

This charter governs real code/test/verification work on the autonomic loop itself — it does not govern shipping it. Any activity whose primary output is a release artifact, a version number change, or changelog content is out of scope for this DMEDI project regardless of how it relates to the loop.

**Boundary repos (named, not owned by this charter):** none beyond the four listed — `~/xaas`, `~/autofde-lab`, `ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack`, `~/clap-noun-verb`.

## 4. Critical to Quality (CTQ) Metrics — Real Measured Baselines

All values below are from real command runs executed this session. Where the source data does not establish a number (e.g., a target, a trend, a cross-run comparison), the field is marked **not measured** rather than estimated.

| # | CTQ | Repo / Source | Measured Value | Target |
|---|-----|----------------|-----------------|--------|
| 1 | MAPE-K/Ash test suite pass rate | `~/xaas`, `mix test test/xaas/operations/ test/mix/tasks/` | 36 tests, 1 property, **0 failures**, 1 excluded; 5.3s total (2.9s async, 2.4s sync) | not measured (no numeric target set this session; qualitative goal is to hold at 0 failures — see §2) |
| 2 | Ash resource real-row coverage | `~/xaas`, `mix xaas.capability_coverage` | 75 total real Postgres-backed Ash resources; 5 with ≥1 real persisted row; 61 with zero rows; 9 errored on count; coverage = **6.7%** | not measured (deferred to Measure/Analyze phase, per §2) |
| 3 | Coverage-gap closed-loop delta | `~/xaas`, `mix xaas.close_coverage_gap` | Ran without crashing; 5 planner classes (`PlannerCandidate`, `PlannerCatalogRequest`, `PlannerMatchRequest`, `PlannerCacheStatsRequest`, `PlannerCacheHotsetRequest`) each end at count 5; closed-loop result for `PlannerCacheHotsetRequest`: before=4, after=5, delta=**+1** | not measured |
| 4 | MAPE-K/Ash file churn (6h) | `~/xaas`, `git log --since="6 hours ago" -- lib/xaas/operations lib/xaas/sparql_bridge.ex lib/mix/tasks/xaas.close_coverage_gap.ex lib/mix/tasks/xaas.safe_generate_migrations.ex` | **14** commits | not measured |
| 5 | autofde-lab Chicago-style pytest suite | `~/autofde-lab`, `pytest tests/fabric/test_phase_h_trigger_chicago.py -q` | collected 4 items, **4 passed**, 0 failed, 0.45s | not measured (qualitative goal: hold at 0 failures) |
| 6 | Phase-H trigger drift detection | `~/autofde-lab`, `phase_h_trigger.run_once()` real run | `drifted: false`; baseline_sha256 == current_sha256 (`5934c2005d7f9f2549548b49e08de7009bd0a182af84c112bb244851fe358a15`); `triggered: false` | not measured |
| 7 | Phase-H coverage-gap probe cadence state | `~/autofde-lab`, same run | `coverage_gap.invoked: false`; `detection_status: "stale_skip_using_prior_observation"`; `skips_since_last_invoke: 2` (of `max_consecutive_skips_before_probe=5`); last real invoke: `closed: true`, `closed_class: "PlannerCacheStatsRequest"`, before=4, after=5, delta=1, gap=1 | not measured |
| 8 | autofde-lab fabric-loop file churn (6h) | `~/autofde-lab`, `git log --since="6 hours ago" -- src/autofde_lab/fabric/phase_h_trigger.py src/autofde_lab/fabric/solve_and_falsify.py src/autofde_lab/receipts/broker.py` | **7** commits | not measured |
| 9 | Connector pack ontology size | `ash-autofde-lab-connector-pack`, `grep -c "aac:AshConnector" ontology.ttl` | **13** `aac:AshConnector` individuals | not measured (ratio to §CTQ 2's 75 total Ash resources is 13/75 ≈ 17.3%, stated here as an arithmetic fact from the two measured counts, not an independently measured or targeted metric) |
| 10 | Connector pack test suite | `ash-autofde-lab-connector-pack`, `pytest scripts/*.py -q` | **3 passed**, 0.37s | not measured (qualitative goal: hold at 0 failures) |
| 11 | Connector pack script churn (6h) | `ash-autofde-lab-connector-pack`, `git log --since="6 hours ago" -- scripts/add_connector.py` | **5** commits | not measured |
| 12 | clap-noun-verb-macros test suite | `~/clap-noun-verb`, `cargo test -p clap-noun-verb-macros` | Unit/integration: **115 passed**, 0 failed, 0 ignored; doctests: 0 passed, 0 failed, 31 ignored | not measured (qualitative goal: hold at 0 failures) |
| 13 | clap-noun-verb full workspace test suite | `~/clap-noun-verb`, `cargo test --workspace` | **840 passed**, **0 failed**, 36 ignored, across 83 test-result lines/targets, all `ok` | not measured (qualitative goal: hold at 0 failed) |
| 14 | clap-noun-verb workspace churn (6h) | `~/clap-noun-verb`, `git log --since="6 hours ago"` | **43** commits | not measured |

**Reading note on CTQ 9's ratio:** 13/75 is an arithmetic derivation from two independently measured counts in this same dataset, not a separately measured or defined CTQ; it is reported for orientation only and carries no target.

## 5. Stakeholders

| Stakeholder | Role in this project | Repo(s) |
|---|---|---|
| xpointsh@gmail.com | Project owner / sole developer of record this session | All four |
| `~/xaas` MAPE-K/Ash mix project | Knowledge + Plan/Execute layer: 75 Ash resources, `xaas.capability_coverage` and `xaas.close_coverage_gap` mix tasks | `~/xaas` |
| `~/autofde-lab` fabric/solver system | Analyze layer: Phase-H drift trigger, coverage-gap probe, Broker/Actuator/PostconditionVerifier receipt chain, 46+ registered solvers (per `pyproject.toml` entry points, as referenced in `pack.toml`) | `~/autofde-lab` |
| `ash-autofde-lab-connector-pack` (ggen-marketplace) | Generated connector: wires Ash resource actions to `clap-noun-verb-deploy` HTTP tool calls against autofde-lab's fabric CLI | `chatman-ecosystem/platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack` |
| `~/clap-noun-verb` workspace | Transport layer: CLI/HTTP surface (`clap-noun-verb-deploy`, `clap-noun-verb-macros`, `clap-noun-verb-any`) carrying `POST /invoke` calls between Ash and autofde-lab | `~/clap-noun-verb` |

No external/third-party stakeholders, customers, or approval bodies are identified in the real data gathered this session; any such stakeholder is **not measured** rather than assumed.

## 6. Risk Register Summary

Risks below are derived only from real, measured evidence gathered this session — not from speculation about failure modes with no data behind them.

| # | Risk | Evidence | Real Measured Severity Signal |
|---|------|----------|-------------------------------|
| 1 | Majority of Ash resources are unexercised in production data | `mix xaas.capability_coverage`: 61 of 75 resources have zero real persisted rows | 81.3% of resources (61/75) — arithmetic from CTQ 2's two measured counts |
| 2 | A subset of Ash resources cannot even be counted | `mix xaas.capability_coverage`: 9 resources errored on count | 12.0% of resources (9/75) — arithmetic from CTQ 2's two measured counts |
| 3 | Analyze-layer re-probing degrades to stale reuse under normal operation | `phase_h_trigger.run_once()` real run: `detection_status: "stale_skip_using_prior_observation"`, 2 of 5 allowed skips already elapsed this cycle | Directly observed on the most recent real run (CTQ 7) |
| 4 | Transport-layer (clap-noun-verb) change velocity substantially outpaces the loop-logic repos it carries | 6-hour commit counts: clap-noun-verb 43 vs. `~/xaas` MAPE-K files 14 vs. autofde-lab fabric-loop files 7 vs. connector pack script 5 | Directly measured (CTQ 4, 8, 11, 14) |
| 5 | Connector pack ontology (13 individuals) covers a small fraction of the real Ash resource surface (75) | `grep -c "aac:AshConnector"` vs. `mix xaas.capability_coverage` total | 13/75 ≈ 17.3% — arithmetic from CTQ 2 and CTQ 9's measured counts |
| 6 | Scope creep into release/versioning work | Standing instruction (§3) explicitly excludes release engineering, version bumps, and changelog work | Not a measured-data risk — a governance risk stated per explicit standing instruction |

No risk likelihood/impact scoring matrix is included: the source data gathered this session contains pass/fail counts, row counts, commit counts, and one real trigger-state snapshot, but no historical trend, incident log, or probability estimate. Any such scoring would be invented, not measured, and is therefore omitted rather than guessed.

---

*This charter is grounded entirely in the four real metrics reports gathered this session across `~/xaas`, `~/autofde-lab`, `ash-autofde-lab-connector-pack`, and `~/clap-noun-verb`. Every numeric value above traces to one of those four reports; every field where the source data did not supply a number is marked "not measured."*
