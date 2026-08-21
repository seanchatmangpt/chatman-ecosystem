# ggen/Igniter-Generated Code — Cross-Pack Maturity Matrix

Content extracted from `ash-igniter-gen-pipeline-pack/MATURITY-MATRIX.md`, which originally
scored 3 unrelated sibling artifacts alongside its own pack in the same tables. This file holds
those 3 artifacts' rows/columns and the cross-artifact commentary; `ash-igniter-gen-pipeline-pack/
MATURITY-MATRIX.md` is now scoped to its own pack only. All content below is preserved verbatim
from the original file — this is a move, not a rewrite.

Assembled from 7 independently-produced metric reports scored against 4 real session artifacts:

1. `ash-gen-resource.txt.tmpl` (`~/xaas/templates-hooks/`)
2. `ash-igniter-gen-pipeline-pack/` (own maturity matrix: `ash-igniter-gen-pipeline-pack/MATURITY-MATRIX.md`)
3. `ash-subproject-pack-generator/` (this repo)
4. `terraform-validate.txt.tmpl` (`~/xaas/templates-hooks/`)

No score below is softened or rounded up from its source report. Where a source rubric used
L0–L4 (Generalization, Safety/Authorization) instead of L1–L5, the level names are preserved
verbatim in the cell and the ordinal column position (1st–5th) is used for placement.

The shared Table 1 (Criteria per Level, by Metric) rubric these scores are graded against lives
in `ash-igniter-gen-pipeline-pack/MATURITY-MATRIX.md` and is not duplicated here.

## Table 2 — Real Scores per Artifact × Metric

| Metric | 1. ash-gen-resource.txt.tmpl | 3. ash-subproject-pack-generator | 4. terraform-validate.txt.tmpl |
|---|---|---|---|
| **Idempotency** | **L3** — `.mix.log` shows literal `Igniter: No proposed content changes!`, but only for one task/target family, no bulk repeat-run receipt. | **L5** — `.ggen-v2/receipt-log.jsonl`: 34/34 `written` on run 1, then 34/34 `skipped` on each of 4 separate re-runs — exact-N match every time. | **L2** — `unless_exists: true` guard present, 88 `.tf.log` files with real `Success! ... valid.` output, but no captured second-run `skipped` receipt log. |
| **Generalization** | **L0** — Hardcoded `mix ash.gen.resource {{...}}` literal; single target, never run against a second. | **L3** — 34 real `asg:AshSubproject` rows drive one template via `for_each`; idempotency confirmed on re-run (34/34 skipped) — L3 fan-out bar met, cross-category bar not. | **L2** — `tv:ValidateTarget`/`tv:terraformModulePath` now drive `sh_after` via SPARQL, replacing the prior hardcoded literal; the unmodified template ran for real against 2 distinct real targets (`tv:ProjectManagementValidate` → `project_management`, `tv:ContributingWorkflowValidate` → `contributing_workflow`), each producing its own real `-chdir` receipt (`.terraform-validate-receipts/{project_management,contributing_workflow}.tf.log`, both `Success! The configuration is valid.`). Meets Table 1's L2 bar exactly (N=2 distinct real targets, same category, receipts from both); not L3 (fan-out is N=2 via 2 individual ontology rows, not a SPARQL `for_each` over N≥10 rows in one run). |
| **Safety / Authorization** | **L1** — (mechanism-wide, shared by all 4 artifacts via `ggen-engine/src/shell_safety.rs`) Denylist of 16 hardcoded substrings before `sh -c`; no allowlist, no isolation; Tera-rendered SPARQL values are interpolated into the command **before** the denylist check, a disclosed shell-injection gap. | Same L1 mechanism/gap applies. | Same L1 mechanism/gap applies. |
| **Verification Evidence** | **L3** — real `.mix.log`/receipt files on disk with real Igniter output, but `~/xaas/.gitignore` excludes `.agp-receipts/`/`.ash-gen-receipts/`; zero tracked, no test suite. | **L3** — strongest within-level evidence: signed, hash-chained receipt log, 34 written + 34×4 skipped confirmed by direct read; but `.ggen-v2/` is not tracked in git, no automated re-verification. | **L2 (unconfirmed L3)** — template correctly wired to a live ontology row, explicitly non-mutating by design, but a populated, real-output `.terraform-validate-receipts/` log was not confirmed in this pass. |
| **Documentation Honesty** | **L1** — one line of body text naming the ontology source; no scope statement, no limitation, no evidence citation beyond the surrounding receipt file. | **L5** — real hex.pm search cited (137 packages, 34 admitted by threshold), plus a named, grounded exclusion: `honeybadger` (2,239,840 downloads) explicitly excluded as a disclosed false positive, not silently dropped. | **L4** — non-mutating design rationale stated honestly (no `apply`, avoiding unpredictable real GitHub resources), explicit named future gap ("no such vocabulary exists in ontology.ttl today"); stops short of L5 because its "proven" claim borrows artifact 1's lineage rather than citing its own dated run count. |
| **Reusability / Portability** | **L1** — mix command and receipt path are hardcoded strings in the template; moving to a second project means editing the template itself. | **L2** — parameterized generation over 34 real hex.pm rows (reuse *within* its own generation loop), but no second consuming project has run this generator against its own data; output still requires per-package domain knowledge a maintainer must add. | **L3** — `sh_after` now reads `{{ terraformModulePath }}` from the SPARQL-selected `tv:ValidateTarget` row instead of a hardcoded literal; the same unmodified template body drove 2 real invocations against 2 distinct real module paths in this project (`modules/integrations/github/project_management`, `modules/integrations/github/contributing_workflow`), both real `terraform validate` calls passing. Meets Table 1's L3 bar (parameterized, proven with >1 real invocation) — capped below L4/L5 because both targets are still rows in the same `~/xaas` project's `ontology.ttl`; no second real consuming project has adopted the vocabulary. |
| **Performance / Efficiency** | **L1** — unmeasured; no real timing was captured against `~/xaas` (out of scope, not touched this run). A structural estimate (~1.4–2.5s/row, extrapolated from terraform-validate's real 1.4s/row) exists but is explicitly not a measurement under the rubric's own L2 bar, so the score does not move. | **L3** — real, repeated, per-stage benchmark: 3 real `ggen sync` runs (1 cold, 2 idempotent) against the actual artifact, `/usr/bin/time -p` wall clock each (0.03s, 0.02s, 0.02s), plus the tool's own `pipeline.*` trace giving a per-stage breakdown (`generate` 5ms, `emit` 9ms→2–3ms, `load`/`validate`/`extract` <1ms) and a per-run file count (34 written / 0 skipped vs. 0 written / 34 skipped) confirming the idempotent-skip path is real. Meets the rubric's L3 bar (deliberate repeatable benchmark, multiple runs, per-task timing, variance noted, defensible baseline) directly against the real artifact, not a proxy. | **L2** — anecdotal single data point: ~63s sequential over 44 rows (~1.4s/row), a real if single wall-clock measurement; not repeated, no variance measured, batching optimization proposed but not implemented. |

## Overall Assessment

**Highest overall: `ash-subproject-pack-generator`.** It is the only artifact to hit the top
of any dimension (Idempotency L5, Documentation Honesty L5) and clears L3 on Generalization and
Verification Evidence — the strongest, most concretely evidenced artifact of the four, anchored
by a real signed/hash-chained receipt log (34 written, then 34/34 skipped across four separate
re-runs).

**Lowest overall: `ash-gen-resource.txt.tmpl` and `terraform-validate.txt.tmpl`.** Both bottom
out at Generalization L0 and Reusability L1 (hardcoded literals, never run against a second
target/project), and both sit at Documentation Honesty L1/L4 or lower engineering maturity than
the two `pack.toml`-driven artifacts on every axis except raw command-level proof. `ash-gen-resource`
is the weakest single artifact overall (L0/L1/L1 on three separate axes, no gap-naming in its docs).

**Weakest metric across the board, plainly: Performance/Efficiency.** Three of four artifacts
(`ash-gen-resource`, `ash-igniter-gen-pipeline-pack`, `ash-subproject-pack-generator`) are fully
**unmeasured (L1)** — no timing was captured even where a real multi-run receipt log already
existed and could have yielded a number for free. Only `terraform-validate` has any timing
evidence at all, and it's a single anecdotal data point (L2), not a repeatable benchmark.

**Second-weakest, and more consequential: Safety/Authorization.** Every artifact runs through
the same shared L1 denylist mechanism (`ggen-engine/src/shell_safety.rs`) — 16 hardcoded bad
substrings checked against a shell string, no allowlist, no sandboxing/isolation, full invoking-process
privileges. Worse, this is a **disclosed, live shell-injection gap**: Tera renders SPARQL/context
values directly into the `sh_before`/`sh_after` command string *before* the denylist check runs,
and the check does not distinguish literal template text from interpolated data. This is a real,
actionable gap affecting all four artifacts uniformly, not a hypothetical one.

**Reusability/Portability is the third systemic gap.** No artifact in this session reaches L4 or
L5 — none has been adopted by a second real consuming project. The most-generalized artifact
(`ash-igniter-gen-pipeline-pack`) caps at L3 by its own `pack.toml`'s admission of single-project
scope. (Note: `ash-igniter-gen-pipeline-pack`'s own score has since moved to L4 — see its own
`MATURITY-MATRIX.md`, "Reusability L3 → L4: real second consuming project (2026-08-21)" — this
overall-assessment paragraph is preserved verbatim from when it was written.)

## Performance/Efficiency Measurement Update (real, this run)

Follow-up reports gathered real timing evidence for `ash-subproject-pack-generator` plus a
structural estimate for the one artifact whose real target (`~/xaas`) remains out of scope
(`ash-gen-resource.txt.tmpl`). (`ash-igniter-gen-pipeline-pack`'s own measurement update lives in
its own `MATURITY-MATRIX.md`.) Real direct measurements are distinguished from the one estimate
below; no score is inflated past what its own evidence supports under Table 1's rubric.

**`ash-subproject-pack-generator` — real direct measurement, promoted L1 → L3.**
Three real `ggen sync` runs (ggen 26.8.18) against the actual pack: run 1 cold
(`packs-out/` removed first, 0.03s, 34 files written, 0 skipped), runs 2–3 idempotent (0.02s
each, 0 written, 34 skipped). The tool's own `pipeline.*` trace lines give a real per-stage
breakdown for run 1 (`generate` 5ms, `emit` 9ms/34 files, `load`/`validate`/`extract` <1ms
each) and show `emit` dropping to 2–3ms with `pipeline.files_generated=0` on the idempotent
runs — the skip path is real, not asserted. All 34 pack directories confirmed present after
all three runs, matching the 34 `asg:AshSubproject` rows in `ontology.ttl`. This is a
deliberate, repeatable benchmark against the real artifact with per-stage timing and variance
noted (0.02s vs 0.03s cold), meeting Table 1's L3 bar directly — not a proxy.

**`ash-gen-resource.txt.tmpl` — estimate only, score unchanged at L1.**
No real timing was captured; running the template requires `~/xaas`, out of scope for this
task under the standing instruction not to modify that directory, and was not run or touched.
A structural estimate was derived instead: both `ash-gen-resource.txt.tmpl` and
`terraform-validate.txt.tmpl` share the same cost shape (`for_each` over a SPARQL row set,
one external cold-process subprocess spawn + `tee`-to-log per row), so terraform-validate's
real, measured 1.4s/row (44 rows, ~63s, per Table 2 above) was used as a
structural floor, with headroom added for BEAM VM boot typically costing as much or more than
a single static Go-binary invocation: **~1.4–2.5s/row (estimate, not a measurement)**. Per
Table 1's own rubric, L2 requires "one real run's wall-clock time observed" — an analogy to
another artifact's real number is not that, so this estimate does not promote the score; it
stays **L1 (unmeasured)**.

## See Also

- `ash-igniter-gen-pipeline-pack/MATURITY-MATRIX.md` — the pack's own maturity matrix (Table 1
  rubric, plus this pack's own Table 2 row and update history)
