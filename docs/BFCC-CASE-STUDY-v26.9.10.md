# BFCC-007 Case Study — v26.9.10 HTN/FOND/HDDL/Koala-Elimination Episode

> **Provenance record.** Assesses the cross-repo claim that `beam4pm`, `ferroplan`, `ex4pm`,
> `ash_ex4pm`, `ggen-marketplace`, and `ggen_igniter` jointly manufacture HTN+FOND planning
> capability while eliminating a `koala-planner` dependency, against the real BFCC 10-gate
> catalog (`catalog/bfcc.toml`) and `scripts/verify_bfcc.py`. This document's job is to be
> checkable, not persuasive: every claim below cites a real command, a real commit SHA, or an
> explicit `UNKNOWN`/`could_not_confirm` where Phase-1 evidence did not reach.

## Verdict, stated first

**Earned standing: `BFCC-PARTIAL`** (exit code 3 from `verify_bfcc.py --json`). Three mandatory
gates — G (Generalized Principles), E (Ephemeralization), T (Trimtab) — have zero Phase-1
evidence and were correctly omitted from the receipt rather than padded with inference; omitting
a mandatory gate forces `PARTIAL`, not `ALIVE`, per the verifier's own logic. Gate Sigma
(Synergy) has real evidence but is an honest falsifier hit: `ash_ex4pm`'s own canary test proves
the claimed four-stage cross-repo chain (ontology → generation → runtime exposure →
verification, reaching all the way to a live `htn_plan` call) is **not yet wired**. Two direct
contradictions are recorded in the receipt rather than smoothed over: `beam4pm` implements HDDL
in its `ferroplan-hddl` crate while the separate `ferroplan` repository refuses HDDL as a
permanent non-goal, and `ash_ex4pm`'s tests assert the planning composition explicitly does not
work end-to-end at this revision.

This is not the rosier narrative a casual read of the individual commit messages would suggest.
Section by section below states what Phase-1 evidence actually confirmed, what it could not
confirm, and where an external narrative is directly corrected by the repo's own artifacts.

## Per-gate: confirmed vs. not confirmed vs. corrected

### C — Comprehensive

**Confirmed:** Phase 1 traced `htn_plan`/`fond_policy` terminology across all 7 subjects
(6 ecosystem repos + `koala-planner`), not just the repo where the feature "lives."

**Not confirmed / falsifier hit:** `beam4pm`'s own `native/ferroplan/crates/ferroplan-hddl` crate
implements HDDL (commit `0434f2d`), while the separate top-level `/Users/sac/ferroplan` repository
explicitly rejects HDDL as out-of-scope (`docs/roadmap-0.17.md`, commit `b1747fb`: "HTN (HDDL)...
OUT — different input languages, different engines; a second front we're not opening"). Whether
`ferroplan-hddl` is a fork/vendor of the `ferroplan` repo or an independently-named crate that
merely shares a word was never reconciled by Phase 1. This is a genuine unexamined downstream
consequence, not a resolved naming coincidence.

### A — Anticipatory

**Confirmed, real and re-runnable:**
- `beam4pm`'s `scripts/gate_no_koala_dependency_check.sh` (commit `e447ac4`) — a live CI gate,
  re-executed in this investigation with real output: three `grep` passes (manifest refs,
  path-dependency-shaped refs, `Command::new`/`System.cmd` shellouts) all reported `ok`, ending
  `PASSED: no real dependency on ~/koala-planner exists in this repo's build graph`.
- `ash_ex4pm`'s canary test `test/integration/beam4pm_via_ex4pm_test.exs:90-100` —
  `refute Beam4pm.supports?(:htn_plan, [])` / `refute function_exported?(AshEx4pm.AutomatedPlanning,
  :htn_plan, 2)` — a pre-declared falsifier that fails loudly the moment `htn_plan` is wrongly
  admitted early.

**Not confirmed:** none of `ferroplan`, `ex4pm`, `ggen-marketplace`, or `ggen_igniter` have a
Phase-1-confirmed pre-declared falsifier for the planning claim specifically — evidence there is
commit-message narrative, not a gate script.

### D — Design

**Confirmed, real runnable artifacts:** `beam4pm`'s regression test
`refuses_a_shortcut_action_unreachable_via_any_decomposition` and WASM dispatch arms
(`c96cabc`, lines 300-301); `ash_ex4pm`'s generated `automated_planning.ex`; `ggen-marketplace`'s
real `beam4pm_pddl.domain.pddl.tmpl`/`.problem.pddl.tmpl` templates (`1ca297a`).

**Falsifier hit:** `ggen-marketplace`'s `planning-federation-pack` (`92cbd4c`) names HTN in its
`pack.toml` description only — zero matching template, query, or ontology file implements HTN
decomposition anywhere in that pack. Prose claim, no artifact.

**Corrected from an external narrative:** the `ex4pm` "13/13" and `ash_ex4pm` "61 tests, 0
failures" figures are commit-author assertions, not independently re-run by this investigation —
they are real *artifacts* (generated code + test files exist) but not real *receipts* (rerun
output does not exist in this evidence set). Treated here as unverified, not as fact.

### S — Science

**Confirmed, real re-run commands with pasted output (this session and Phase 1 combined):**
- Manifest/lockfile discovery + `koala` grep across `Cargo.toml`/`Cargo.lock`/`mix.exs`/
  `mix.lock` (no `package.json`/`requirements.txt` exist in this repo): zero hits.
- Full source-tree `grep -rIn koala` (excluding `.git`/`node_modules`/`_build`/`deps`/`target`/
  `.claude`): 39 lines matched, none a dependency — comments mirroring koala-planner's HDDL
  syntax, a not-yet-done wiring design doc, the gate script itself, and unrelated biomedical
  ontology text (`uberon.owl`/`mondo.owl`) about the animal.
- Subprocess-shellout grep for a `koala` binary invocation: zero real invocations.
- `scripts/gate_no_koala_dependency_check.sh` re-run live: `PASSED`.
- `ferroplan` repo's PDDL3 `:constraints` refusal test re-run live: `cargo test -p ferroplan
  --test constraints` → `hatch_restores_the_blanket_rejection ... ok`,
  `cli_text_path_enforces_too ... ok` (2/2 passed). This is the only unsupported-planning-class
  refusal with a real runnable test found — it covers PDDL3 trajectory constraints specifically,
  not temporal/durative/LTL/numeric-fluents (those are implemented features in `ferroplan`, not
  refused classes).
- `ggen_igniter` determinism re-run live: two independent `mix ggen_igniter.sync` runs into a
  gitignored `tmp_out/`, `diff -r` exit code 0 (byte-identical output across runs); scratch dirs
  removed afterward, no tracked files touched.
- `verify_bfcc.py --receipt` re-run live against a synthetic missing-`inventory_examined`
  fixture: `{"standing": "REFUSED:MISSING_INVENTORY"}`, exit code 2 — matches
  `tests/test_bfcc.py::test_missing_inventory_refused`.

**Not confirmed / explicitly flagged unverified:** `ex4pm`'s "13/13", `ash_ex4pm`'s "61 tests, 0
failures", and `ex4pm`'s "`mix compile --warnings-as-errors clean`" claims are commit-message
assertions from the original authors, not independently re-run here. Per this file's own
discipline (and the user's global testing/evidence rules), these are named as UNVERIFIED and
excluded from S's supporting evidence rather than cited as fact.

### G — Generalized Principles

**No Phase-1 evidence exists.** Nothing in Phase 1 examined whether `ex4pmb:htn_plan`,
`bpm:opVerificationClass`, `ex4pmb:AdmittedBeam4pmService`, etc. duplicate an existing public
ontology term (`prov:`, `pplan:`, `earl:`, `skos:`) or are genuinely new. The rename commit
`b21aa28` (`ferroplan_hierarchical_plan` → `htn_plan`) shows local vocabulary hygiene toward
standard planning terminology, but says nothing about public-ontology reuse. **Status: UNKNOWN,
not estimated.**

### Sigma — Synergy

**Confirmed real, repo-local pairwise links:**
- ontology → generation: `ex4pm`'s `b21aa28` (ontology rename regenerates route table),
  `beam4pm`'s `c96cabc` (ontology.ttl → three-language facade regeneration).
- generation → runtime exposure: within `beam4pm` alone (dispatch arms `"htn_plan" =>
  op_htn_plan`, `"fond_policy" => op_fond_policy`) and within `ex4pm` alone (route table with
  `status: :live | :forward_declared`).
- runtime exposure → verification: within `ex4pm` alone (`e9ddf01`'s refusal test for
  `forward_declared` routes) and `ash_ex4pm` alone (`7c24a09`'s canary test).

**Falsifier hit, not partial credit:** no composed, cross-repo integration test invokes
`beam4pm`'s `htn_plan` op through `ex4pm`'s admission layer through `ash_ex4pm`'s generated Ash
resource end-to-end. `ash_ex4pm`'s own test proves the opposite of composition currently
working: `refute function_exported?(AshEx4pm.AutomatedPlanning, :htn_plan, 2)`, with commit
`59eb76f` stating the admission mechanism "projects zero live planning operations (htn_plan/
fond_policy not yet admitted upstream)." Three of three pairwise links are real; the full
four-stage chain, at the assessed revisions, is confirmed **not wired**.

### E — Ephemeralization

**No Phase-1 evidence exists.** No resource cost (tokens, compute, human time) is paired with a
verified capability delta anywhere in the evidence set. The closest resource-adjacent fact —
`beam4pm`'s `c96cabc` regenerating three language facades from one ontology edit — has no
recorded LOC diff, `git diff --stat`, or time/token cost. η cannot be computed with only one
unquantified data point and no denominator. **Status: UNKNOWN, not estimated.**

### T — Trimtab

**No Phase-1 evidence exists** in ratio form. The only traced chain with named artifacts —
`beam4pm`'s ontology rename `b21aa28` → 2 named downstream artifacts regenerated in `ex4pm`
(`lib/ex4pm/engine/beam4pm.ex` route table, `test/engine_beam4pm_test.exs`) — is a real raw count
(1 ontology edit → 2 downstream files, per commit message, not a re-run diff), but the size of
the source ontology diff itself was never measured, so λ (downstream/Δcanonical) cannot be
computed as a ratio. **Status: UNKNOWN (raw count only, not a leverage ratio).**

### W — World

**Special-attention finding:** `koala-planner` (`/Users/sac/koala-planner`, HEAD `6623ec2`) is a
real, independently confirmed pre-existing artifact — a genuine ANU-authored (Anthony Gambale,
Mohammad Yousefi, Harrison Oates), 158-commit Rust+Python FOND-HTN solver, forked to
`seanchatmangpt/koala-planner`. `beam4pm`'s commit `692224f` is a real prose design doc, dated
one day before the `no-koala-dependency` gate script, that explicitly *proposes* wiring
`koala-planner` in — the one artifact resembling "discovery before new work."

**Not confirmed:** whether the design doc or any later session actually attempted a WASM compile
or produced working glue code was not checked. `koala-planner`'s own git history has **zero**
references to `beam4pm`/`ferroplan`/`ex4pm` (confirmed by grep across `git log --all` and
tracked-file contents) — the "discovery" relationship, if real, is one-directional and
undocumented on the koala-planner side. No repo produced an itemized dependency/cost/resource
inventory artifact (W's required shape). **Status: UNCONFIRMED, evidence thin** — suggestive
timing only, not a confirmed inventory act.

### I — Integrity

**Confirmed, real and load-bearing refusal commits:**
- `beam4pm`'s `ast.rs:16-19` / `parser.rs:754-755,826-827` refuse `:durative-action`/`:functions`
  with typed `ParseError::UnsupportedConstruct`, backed by a real test
  `refuses_durative_action_section_with_typed_error` (`c0ea01d`).
- `ferroplan`'s `docs/roadmap-0.17.md:15-18` refuses HTN/HDDL/RDDL by direct decision (`b1747fb`).
- `ash_ex4pm`'s canary test is itself a refusal-by-design.

**Direct contradiction within the evidence itself:** `beam4pm` and `ferroplan` disagree on
whether HDDL is refused — `beam4pm` implements it, `ferroplan` refuses it as a permanent
non-goal. A single unqualified ecosystem-level standing ("HDDL is refused" or "HDDL is admitted")
would be directly contradicted by one of the two repos' own evidence. Per-repo, narrowly scoped
claims (e.g., "beam4pm refuses durative actions, confirmed by test") are I-clean; a blanket
"the ecosystem delivers HTN/FOND planning" claim is not, and citing the unverified 13/13 or 61/0
test counts as settled fact would itself be an I violation.

## Falsifiers actually executed, real results

| # | Falsifier | Command | Real result |
|---|---|---|---|
| 1 | Missing-inventory refusal | `python3 scripts/verify_bfcc.py --root . --receipt <fixture w/ inventory_examined deleted> --json` | `{"standing": "REFUSED:MISSING_INVENTORY"}`, exit 2 — matches `test_missing_inventory_refused` |
| 2 | Koala-dependency absence, ecosystem repo | manifest/lockfile find + grep, full-tree grep, subprocess-shellout grep, live gate-script run | Zero real dependency/binary-invocation hits; only prose/comment/unrelated-ontology matches; gate script `PASSED` |
| 3 | Unsupported-constraint refusal (ferroplan) | `cargo test -p ferroplan --test constraints` | 2/2 tests pass (`hatch_restores_the_blanket_rejection`, `cli_text_path_enforces_too`) — PDDL3 `:constraints` refusal real; temporal/durative/numeric-fluent are implemented, not refused, in this repo |
| 4 | ggen_igniter determinism | two independent `mix ggen_igniter.sync` runs into gitignored `tmp_out/`, `diff -r` | exit 0 — byte-identical output; scratch cleaned, no tracked files touched |

## Composite-subject boundary decision

Question: does `verify_bfcc.py`'s schema support a composite multi-repo `subject`/`revision`
string spanning 7 repositories? **Answer: yes, already, with zero code change.**
`evaluate_receipt()` (`scripts/verify_bfcc.py:111-129`) reads `subject`/`revision` as opaque,
untyped strings — no regex, no SHA-shape check, no length constraint. The only logic applied is
a `STANDING_TRANSFERRED` equality check between the receipt-level value and any
`evidence_per_gate[*].subject`/`.revision` sub-fields, when present. `catalog/bfcc.toml`'s
`[receipt].required_fields` lists `"subject"`/`"revision"` as required *keys*, with no value-shape
schema anywhere. A composite string —
`beam4pm+ferroplan+ex4pm+ash_ex4pm+ggen-marketplace+ggen_igniter+koala-planner@v26.9.10-...` for
subject, `beam4pm=<sha>;ferroplan=<sha>;...` for revision — passes cleanly as long as every
per-gate sub-field that includes `subject`/`revision` echoes the same composite string verbatim.
No `catalog/bfcc.toml` or `scripts/verify_bfcc.py` change was made; none was needed.

## Real eta/lambda/sigma findings

Computed by `scripts/bfcc_benchmark.py --receipts .artifacts/bfcc/receipts.jsonl --json` after
appending BFCC-007's ledger line (commit `bdce2fd4`):

```json
{"problem_classes": {"cross-repo-htn-fond-capability-claim": {"receipt_count": 1, "eta": {"n": 0, "direction": "INSUFFICIENT_DATA", "slope": null, "values": []}, "lambda": {"n": 0, "direction": "INSUFFICIENT_DATA", "slope": null, "values": []}}}}
```

- **η (Ephemeralization):** `INSUFFICIENT_DATA` — one receipt in this problem class, no
  resource-cost measurement recorded (matches the G/E/T gate findings above: no Phase-1 evidence
  contains a resource vector). No synthetic second receipt was manufactured to fabricate a trend.
- **λ (Trimtab):** `INSUFFICIENT_DATA` — same reason; only a raw downstream-artifact count exists
  (see gate T above), not a ratio.
- **Σ (Synergy):** not a benchmark-computed quantity here; scored directly at the gate level as a
  **falsifier hit** (see Sigma section) — the claimed four-stage cross-repo chain is real
  pairwise but not composed end-to-end.

The receipt's `resource_vector` fields are recorded as honest `"UNKNOWN"` placeholders and
`verified_capability_delta`/`canonical_information_delta` as `null` — no fabricated resource cost
or capability delta exists in the Phase-1 evidence, so none was invented for the ledger.

## Claims from a hypothetical rosier external narrative, corrected

- *"koala-planner was discovered and its capability absorbed"* — **not corroborated.**
  `koala-planner`'s own history shows zero awareness of the ecosystem; only a one-day-prior
  design doc suggests it was considered, and no glue/WASM-compile attempt was checked or found.
- *"HTN/FOND planning works end-to-end across the ecosystem"* — **not corroborated; contradicted**
  by `ash_ex4pm`'s own test.
- *"13/13" and "61 tests, 0 failures" as settled facts* — **not independently re-run**;
  author-claimed only, carried here as unverified.
- *"HDDL is a consistently-scoped decision across the ecosystem"* — **not corroborated;
  contradicted**: `beam4pm` implements it, `ferroplan` refuses it as a permanent non-goal.
- *"ggen_igniter/GGI as a dedicated, named planning-generation tool"* — **not corroborated** in
  `beam4pm`, `ferroplan`, `ggen-marketplace`, or `ggen_igniter` itself; only confirmed as a
  general-purpose generation mechanism in `ex4pm`/`ash_ex4pm`, not planning-specific there either.
- *"A canonical-state/deduplication bug fix in planner BFS/blocksworld code"* — **not
  corroborated** in `beam4pm`, `ex4pm`, `ash_ex4pm`, `ggen-marketplace`, or `ggen_igniter` (all
  "canonical"/"dedup" hits found are in unrelated ontology/OCEL/formatter/digest domains);
  `ferroplan` has real canonical-state-keying work, but in A* search sites, not BFS, and not tied
  to blocksworld.
- *"CI passing at current HEAD across the ecosystem"* — **not corroborated.**
  `ggen-marketplace`'s exact-HEAD CI is confirmed FAILING; `beam4pm`'s most recently evaluated
  commit shows 3 failing workflows; `ex4pm`'s most recent main-branch CI shows failure;
  `ferroplan` shows a repeated-failure trend; `ash_ex4pm` has no CI configured at all; exact-HEAD
  CI status is unconfirmed (no run recorded yet) for `beam4pm`, `ex4pm`, and `ggen_igniter`.

## Closing summary table

| Gate | Evidence | Result |
|---|---|---|
| C (Comprehensive) | 7-repo trace of htn_plan/fond_policy; ferroplan-repo vs. ferroplan-hddl-crate naming never reconciled | PARTIAL |
| A (Anticipatory) | 2 real pre-declared falsifiers (beam4pm gate script, ash_ex4pm canary), not ecosystem-wide | PARTIAL |
| D (Design) | Real artifacts in beam4pm/ash_ex4pm/ggen-marketplace(PDDL); ggen-marketplace HTN claim is prose-only | PARTIAL |
| S (Science) | 4 real live falsifier re-runs (this session) + koala/CI evidence; several test-count claims correctly excluded as unverified | PARTIAL |
| G (Generalized Principles) | No public-ontology-reuse examination anywhere in Phase 1 | UNKNOWN — omitted |
| Sigma (Synergy) | 3/3 pairwise links real repo-locally; full 4-stage cross-repo chain proven NOT wired by ash_ex4pm's own test | FALSIFIER HIT |
| E (Ephemeralization) | No resource-cost measurement recorded anywhere | UNKNOWN — omitted |
| T (Trimtab) | Only a raw artifact count (1→2), no Δcanonical size measured, no ratio | UNKNOWN — omitted |
| W (World) | koala-planner real pre-existing artifact; design-doc timing suggestive only; no itemized inventory artifact | UNCONFIRMED / thin |
| I (Integrity) | Real refusal commits (beam4pm durative/functions, ferroplan HTN/HDDL/RDDL); beam4pm vs. ferroplan directly contradict on HDDL | PARTIAL / CONTRADICTION RECORDED |

**Overall receipt standing:** `BFCC-PARTIAL`, exit code 3, recorded at
`.artifacts/bfcc/receipts/bfcc-007-v26.9.10.json`, commit `b7bd125aab6f4bec54a9fa7b797f792b23e63dd4`.
Benchmark ledger line appended at commit `bdce2fd4f2e025af50cf00d7951e5f384cbbfb1c`
(`.artifacts/bfcc/receipts.jsonl`), benchmark run returning `INSUFFICIENT_DATA` for both η and λ
on a single-receipt problem class — the honest result, not a manufactured trend.

## See Also

- `docs/jira/v26.9.10/BFCC-007.md` — the ticket this case study resolves
- `.artifacts/bfcc/receipts/bfcc-007-v26.9.10.json` — the real receipt this document narrates
- `.artifacts/bfcc/receipts.jsonl` — the benchmark ledger BFCC-007 appended to
- `catalog/bfcc.toml` — the 10-gate catalog and required-fields schema referenced throughout
- `scripts/verify_bfcc.py` / `scripts/bfcc_benchmark.py` — the verifier and benchmark tools whose
  real output is cited above
