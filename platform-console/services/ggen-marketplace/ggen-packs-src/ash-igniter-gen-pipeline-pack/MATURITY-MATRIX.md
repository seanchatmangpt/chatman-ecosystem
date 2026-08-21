# ggen/Igniter-Generated Code — 5×7 Maturity Matrix

Assembled from 7 independently-produced metric reports scored against 4 real session artifacts:

1. `ash-gen-resource.txt.tmpl` (`~/xaas/templates-hooks/`)
2. `ash-igniter-gen-pipeline-pack/` (this repo)
3. `ash-subproject-pack-generator/` (this repo)
4. `terraform-validate.txt.tmpl` (`~/xaas/templates-hooks/`)

No score below is softened or rounded up from its source report. Where a source rubric used
L0–L4 (Generalization, Safety/Authorization) instead of L1–L5, the level names are preserved
verbatim in the cell and the ordinal column position (1st–5th) is used for placement.

## Table 1 — Criteria per Level, by Metric

| Metric | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 |
|---|---|---|---|---|---|
| **Idempotency** | Unguarded regeneration: no `unless_exists` guard, no independently idempotent underlying command; re-run always mutates. | File-existence-guarded, single case proven: `unless_exists: true` (or equivalent) makes a second run a no-op at the file level, for one real target. | Guarded + underlying command independently idempotent, single case: real captured second-run output shows "no diff" (e.g. `Igniter: No proposed content changes!`) for one command variant. | Guarded + idempotent command, generalized ≥2 inputs: parameterized template, no-op-on-rerun evidenced for ≥2 structurally distinct real invocations, each with its own real log. | Fleet-scale idempotency proven under repeated bulk sync: N≥10 real targets from one SPARQL query, ≥2 additional re-runs each showing 100% `skipped` matching N exactly. |
| **Generalization** | (L0) Hardcoded, unproven: one target, one hardcoded literal, no parameter axis, never run against a second target. | (L1) Parameterized, unproven: varying axis is a real ontology property/template variable, but only ever run against N=1 real target. | (L2) Proven against N=2 distinct real targets, same category: real run (not dry-run) of the same template against 2 distinct real parameter values, receipts from both. | (L3) Proven fan-out at scale (N≥10), single category: SPARQL `for_each` over a real multi-row dataset produces N≥10 real distinct outputs in one run, per-row receipts. | (L4) Proven across categories + idempotency confirmed on re-run: distinct target categories, or an L3-scale fan-out re-run identically with 100% skip confirmed, real logs both times. |
| **Safety / Authorization** | (L0) No checks: any string in `sh_before`/`sh_after` runs via `sh -c` unconditionally. | (L1) Denylist: fixed list of known-bad substrings checked before exec; case-insensitive; false negatives pass silently. | (L2) Allowlist / structural validation: only a fixed set of permitted commands/binaries, or parsed-argv check, rejecting unknown constructs by default. | (L3) Isolated execution: allowlist/argv validation plus reduced privilege/isolation (container, restricted user, seccomp, no egress) so unanticipated bad commands are contained. | (L4) Provable non-destructive guarantee: every invocation verified via sandboxing + effect analysis (dry-run diffing, capability-scoped access, or formal proof) incapable of destructive/exfiltrating side effects before real execution. |
| **Verification Evidence** | Claim on faith: no receipt, no log, no test; only a template/doc asserting it "works." | Single manual run, discarded: a real invocation happened once but output wasn't captured to a durable file, or only to a gitignored scratch path, no re-run, no test. | Real receipt/log captured on disk, not committed: an actual command ran and its output exists as a file, but the directory is gitignored/untracked; no automated re-check. | Committed evidence, not a re-runnable automated suite: receipts/logs/code checked into git, but verification was a one-off manual invocation, no `mix test`-style suite. | Committed, automated, re-runnable test suite + receipt logs: both a real automated test suite and real receipt/log artifacts are in version control; CI reproduces verification independently. |
| **Documentation Honesty** | No docs, or descriptive only: states what the artifact does; no discussion of proven vs. assumed, no limitations, no evidence. | Scope stated, unevidenced: claims a proven/working state but backs it with assertion only — no concrete numbers, dates, log paths, or command output cited. | Scope + evidence: proven claims backed by specific, checkable evidence (dates, counts, file paths, real command output) — but no limitations or exclusions named. | Scope + evidence + gaps named: all of Level 3, plus specific known limitations/exclusions/future-scope items named honestly, not just implied. | Full: all of Level 4, and the gaps themselves are evidence-grounded (a named reason/number for each exclusion), with an explicit proven-vs-not-yet-proven line. |
| **Reusability / Portability** | Project-bound: paths, module names, commands are literal strings hardcoded in the template body; adopting elsewhere means editing core logic. | Parameterized, single-instance: core logic reads variable parts from ontology facts instead of literals, but only one concrete project/context has ever driven it. | Parameterized, multi-facet, single-project: vocabulary generalizes along more than one axis, proven with more than one real invocation — but all from the same project's ontology. | Vocabulary published, adoption path documented, not yet exercised: project-agnostic vocabulary plus an honest statement of what a second project would need to do — but no second project has done it. | Cross-project proven: a second, genuinely distinct real consuming project has adopted the same template/vocabulary by adding only its own ontology facts, with a real run's receipts as evidence. |
| **Performance / Efficiency** | Unmeasured: no timing captured anywhere; throughput/latency unknown, not just unstated. | Anecdotal single data point: one real run's wall-clock time observed, giving a rough rate, but not repeated, no isolation from noise, no per-phase breakdown. | Measured baseline: a deliberate, repeatable benchmark — multiple runs, per-row/per-task timing recorded, variance noted, a defensible "before" number as an optimization target. | Optimized with before/after: a real change (e.g. batching invocations into fewer process spawns) implemented and measured against the Level 3 baseline, real before/after numbers. | Continuously benchmarked: performance regression-tested in CI/pipeline on every change, numbers tracked over time, alerts on regression. |

## Table 2 — Real Scores per Artifact × Metric

| Metric | 1. ash-gen-resource.txt.tmpl | 2. ash-igniter-gen-pipeline-pack | 3. ash-subproject-pack-generator | 4. terraform-validate.txt.tmpl |
|---|---|---|---|---|
| **Idempotency** | **L3** — `.mix.log` shows literal `Igniter: No proposed content changes!`, but only for one task/target family, no bulk repeat-run receipt. | **L4** — Generalized via `agp:mixTask`; two distinct real task logs (`ash.gen.resource`, `ash.extend`), but only one carries the explicit no-diff line; no fleet-scale repeat run. | **L5** — `.ggen-v2/receipt-log.jsonl`: 34/34 `written` on run 1, then 34/34 `skipped` on each of 4 separate re-runs — exact-N match every time. | **L2** — `unless_exists: true` guard present, 88 `.tf.log` files with real `Success! ... valid.` output, but no captured second-run `skipped` receipt log. |
| **Generalization** | **L0** — Hardcoded `mix ash.gen.resource {{...}}` literal; single target, never run against a second. | **L2** — `agp:mixTask`/`agp:mixArgs` real datatype properties; proven against 2 distinct real mix tasks in same project (same category), so caps below L4. | **L3** — 34 real `asg:AshSubproject` rows drive one template via `for_each`; idempotency confirmed on re-run (34/34 skipped) — L3 fan-out bar met, cross-category bar not. | **L2** — `tv:ValidateTarget`/`tv:terraformModulePath` now drive `sh_after` via SPARQL, replacing the prior hardcoded literal; the unmodified template ran for real against 2 distinct real targets (`tv:ProjectManagementValidate` → `project_management`, `tv:ContributingWorkflowValidate` → `contributing_workflow`), each producing its own real `-chdir` receipt (`.terraform-validate-receipts/{project_management,contributing_workflow}.tf.log`, both `Success! The configuration is valid.`). Meets Table 1's L2 bar exactly (N=2 distinct real targets, same category, receipts from both); not L3 (fan-out is N=2 via 2 individual ontology rows, not a SPARQL `for_each` over N≥10 rows in one run). |
| **Safety / Authorization** | **L1** — (mechanism-wide, shared by all 4 artifacts via `ggen-engine/src/shell_safety.rs`) Denylist of 16 hardcoded substrings before `sh -c`; no allowlist, no isolation; Tera-rendered SPARQL values are interpolated into the command **before** the denylist check, a disclosed shell-injection gap. | Same L1 mechanism/gap applies (all hooks route through the same `check_shell_command_safe` → `sh -c` path). | Same L1 mechanism/gap applies. | Same L1 mechanism/gap applies. |
| **Verification Evidence** | **L3** — real `.mix.log`/receipt files on disk with real Igniter output, but `~/xaas/.gitignore` excludes `.agp-receipts/`/`.ash-gen-receipts/`; zero tracked, no test suite. | **L3** — two distinct real task logs prove generalization, but same VCS gap; the committed test suite that exists (`capability_liveness_receipt_test.exs`) tests the *generated resource*, not the pipeline itself. | **L3** — strongest within-level evidence: signed, hash-chained receipt log, 34 written + 34×4 skipped confirmed by direct read; but `.ggen-v2/` is not tracked in git, no automated re-verification. | **L2 (unconfirmed L3)** — template correctly wired to a live ontology row, explicitly non-mutating by design, but a populated, real-output `.terraform-validate-receipts/` log was not confirmed in this pass. |
| **Documentation Honesty** | **L1** — one line of body text naming the ontology source; no scope statement, no limitation, no evidence citation beyond the surrounding receipt file. | **L5** — evidence-cited proven claim (2 real tasks, real receipt stdout) plus a dated, grounded gap: "only ONE real consuming project ... a real audit (2026-08-20) found only 5 ontology.ttl files and 1 mix.exs project locally." | **L5** — real hex.pm search cited (137 packages, 34 admitted by threshold), plus a named, grounded exclusion: `honeybadger` (2,239,840 downloads) explicitly excluded as a disclosed false positive, not silently dropped. | **L4** — non-mutating design rationale stated honestly (no `apply`, avoiding unpredictable real GitHub resources), explicit named future gap ("no such vocabulary exists in ontology.ttl today"); stops short of L5 because its "proven" claim borrows artifact 1's lineage rather than citing its own dated run count. |
| **Reusability / Portability** | **L1** — mix command and receipt path are hardcoded strings in the template; moving to a second project means editing the template itself. | **L3** — real multi-axis proof (2 distinct tasks) via `agp:mixTask`/`agp:mixArgs`, but `pack.toml` itself states "proven against exactly ONE real consuming project (~/xaas)" — no second project exists yet. | **L2** — parameterized generation over 34 real hex.pm rows (reuse *within* its own generation loop), but no second consuming project has run this generator against its own data; output still requires per-package domain knowledge a maintainer must add. | **L3** — `sh_after` now reads `{{ terraformModulePath }}` from the SPARQL-selected `tv:ValidateTarget` row instead of a hardcoded literal; the same unmodified template body drove 2 real invocations against 2 distinct real module paths in this project (`modules/integrations/github/project_management`, `modules/integrations/github/contributing_workflow`), both real `terraform validate` calls passing. Meets Table 1's L3 bar (parameterized, proven with >1 real invocation) — capped below L4/L5 because both targets are still rows in the same `~/xaas` project's `ontology.ttl`; no second real consuming project has adopted the vocabulary. |
| **Performance / Efficiency** | **L1** — unmeasured; no real timing was captured against `~/xaas` (out of scope, not touched this run). A structural estimate (~1.4–2.5s/row, extrapolated from terraform-validate's real 1.4s/row) exists but is explicitly not a measurement under the rubric's own L2 bar, so the score does not move. | **L2** — real repeated benchmark (n=10, release build, `sync_e2e-8bf959ebe379a952`) via the closest real proxy (no dedicated `cargo bench` target exists): mean 0.211s, range 0.200–0.230s, variance noted. Capped at L2, not L3, because it benchmarks the shared sync-engine mechanism, not this pack's own `agp:mixTask` subprocess invocations, and records one whole-cycle time rather than a per-task/per-row breakdown. | **L3** — real, repeated, per-stage benchmark: 3 real `ggen sync` runs (1 cold, 2 idempotent) against the actual artifact, `/usr/bin/time -p` wall clock each (0.03s, 0.02s, 0.02s), plus the tool's own `pipeline.*` trace giving a per-stage breakdown (`generate` 5ms, `emit` 9ms→2–3ms, `load`/`validate`/`extract` <1ms) and a per-run file count (34 written / 0 skipped vs. 0 written / 34 skipped) confirming the idempotent-skip path is real. Meets the rubric's L3 bar (deliberate repeatable benchmark, multiple runs, per-task timing, variance noted, defensible baseline) directly against the real artifact, not a proxy. | **L2** — anecdotal single data point: ~63s sequential over 44 rows (~1.4s/row), a real if single wall-clock measurement; not repeated, no variance measured, batching optimization proposed but not implemented. |

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
scope.

## Performance/Efficiency Measurement Update (real, this run)

Three follow-up reports gathered real timing evidence for the three artifacts in this repo's
scope (`ash-subproject-pack-generator`, `ash-igniter-gen-pipeline-pack`) plus a structural
estimate for the one artifact whose real target (`~/xaas`) remains out of scope
(`ash-gen-resource.txt.tmpl`). Real direct measurements are distinguished from the one estimate
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

**`ash-igniter-gen-pipeline-pack` — real direct measurement (proxy), promoted L1 → L2.**
No dedicated `cargo bench` target exists for template-rendering/`for_each` (checked
`Cargo.toml`: 12 `[[bench]]` entries, none render/sync-specific). Used the closest real proxy:
`crates/ggen-engine/tests/sync_e2e.rs::first_sync_writes_second_sync_skips_unchanged_and_hash_is_stable`,
a real Chicago-style e2e test (real tempdir, real oxigraph store, real Tera render, real SPARQL
query, real first-write + second-write-skip cycle) — the same engine machinery `ggen sync` uses,
without the `mix` subprocess step. Real release-build binary
(`target/release/deps/sync_e2e-8bf959ebe379a952`), invoked directly 10 times with `--exact`:
`0.22s 0.23s 0.21s 0.22s 0.22s 0.20s 0.20s 0.20s 0.21s 0.20s` — n=10, mean=0.211s,
min=0.200s, max=0.230s. Capped at L2 rather than L3: it is a whole-pipeline proxy number (no
per-phase split of render vs. I/O vs. SPARQL query), and it measures the shared sync-engine
mechanism rather than this pack's own `agp:mixTask` subprocess invocations directly.

**`ash-gen-resource.txt.tmpl` — estimate only, score unchanged at L1.**
No real timing was captured; running the template requires `~/xaas`, out of scope for this
task under the standing instruction not to modify that directory, and was not run or touched.
A structural estimate was derived instead: both `ash-gen-resource.txt.tmpl` and
`terraform-validate.txt.tmpl` share the same cost shape (`for_each` over a SPARQL row set,
one external cold-process subprocess spawn + `tee`-to-log per row), so terraform-validate's
real, measured 1.4s/row (44 rows, ~63s, per MATURITY-MATRIX line above) was used as a
structural floor, with headroom added for BEAM VM boot typically costing as much or more than
a single static Go-binary invocation: **~1.4–2.5s/row (estimate, not a measurement)**. Per
Table 1's own rubric, L2 requires "one real run's wall-clock time observed" — an analogy to
another artifact's real number is not that, so this estimate does not promote the score; it
stays **L1 (unmeasured)**.

## Generalization Update — ordered task-graph fan-out (real, 2026-08-20)

`ash-igniter-gen-pipeline-pack` extended with `agp:rank` (asserted topological position) and
`ORDER BY ?rank` in the template's SPARQL query. Validated in two stages:

**`playground/` (fixture-only, no real Ash project):** real `ggen sync` against
`examples/02-full-chain.ttl` (domain rank 0, resource rank 1, extend rank 2, migration
rank 3). The four `sh_after mix ...` invocations' real stdout stream (all four failed with
`Mix task could not be found`, expected — `playground/` has no real `mix.exs`) appeared in
exact ascending-rank order: `ash.gen.domain` → `ash.gen.resource` → `ash.extend` →
`ash_postgres.generate_migrations`. Confirms `for_each` executes `sh_after` in
`ORDER BY`-determined row order, not incidental store order — the core assumption this
extension depends on.

**`~/xaas` (real project, real run, 2026-08-20):** added a real rank-ordered chain
targeting the already-proven `CapabilityLivenessReceipt` / `Xaas.Operations` target: a new
`agp:rank 0` domain row (`ash.gen.domain`) and a new `agp:rank 3` migration row
(`ash_postgres.generate_migrations`), alongside the existing `agp:rank 1`/`agp:rank 2`
resource/extend rows. Real `ggen sync` run wrote 2 new receipts
(`.agp-receipts/Operations-ash.gen.domain.txt`,
`.agp-receipts/CapabilityLivenessReceipt-ash_postgres.generate_migrations.txt`) and skipped
the 2 pre-existing ones (`unless_exists`). A second real `ggen sync` run confirmed all 4 rows
skip (100% idempotent re-run under the new `ORDER BY`-augmented query).

Two real, disclosed gotchas from this run, not smoothed over:
- `ash.gen.domain` against an already-existing domain does **not** report Igniter's usual
  `Igniter: No proposed content changes!` no-op message — it reports
  `Issues: * lib/xaas/operations.ex: File already exists` instead. Functionally idempotent
  (no file was overwritten, `unless_exists` at the receipt level still prevents a
  second real invocation), but a different real message shape than `ash.gen.resource`'s.
- `ash_postgres.generate_migrations` is **not scoped to the target module** — it inspects the
  whole project's real schema drift. This run's real invocation picked up unrelated,
  pre-existing drift already present in `~/xaas`'s dirty working tree (a real interactive
  prompt: `Are you renaming tokens.extra_data to tokens.encrypted_extra_data? [Yn]`) and
  printed intent to create a migration file covering that drift, not just
  `CapabilityLivenessReceipt` — **but the file was never actually written.** Verified by
  direct filesystem check after the run: neither
  `priv/repo/migrations/20260821021533_add_capability_liveness_receipt.exs` nor its paired
  resource-snapshot JSON exist on disk, despite the log's `* creating ...` line. The real
  explanation: under `sh -c`-piped non-interactive execution, the `[Yn]` prompt received no
  real stdin, and Igniter printed its *intended* action before that prompt resolved rather
  than after — so `sh_after`'s captured log is not a reliable record of what actually
  happened for a task with an interactive confirmation step. The `.agp-receipts/` guard file
  was still written (marking the row "done" for future `unless_exists` skips), which is
  itself a real correctness gap: this task's receipt can indicate success when the
  underlying mix task silently produced nothing. Anyone driving `ash_postgres.generate_migrations`
  (or any Igniter task with a real interactive confirmation path) via unattended `sh_after`
  should either run it against a target/state guaranteed to hit no interactive prompt, or
  treat its receipt as unverified until a human confirms the real output file exists.

**Score:** Generalization moves from **L2 → L3** for `ash-igniter-gen-pipeline-pack` — real
ordered fan-out across 4 distinct `agp:mixTask` values (domain/resource/extend/migration),
confirmed ascending-rank execution order (both in `playground/` and against real `~/xaas`),
and a confirmed idempotent re-run of the receipt-guard mechanism. Qualified: 3 of the 4 task
categories (domain, resource, extend) verifiably completed their real work; the 4th
(migration) verifiably *ran* but did not verifiably *complete* — see the interactive-prompt
gotcha above — so this proves the mechanism dispatches 4 distinct real mix invocations in the
right order, not that all 4 reliably reach real output unattended. Does not reach L4 (would
require proof across genuinely distinct target *categories*, not just task types against one
target) or cross-project reuse (still 0/N second projects, per the pack's existing
Reusability L3 cap).

## End-to-end receipt audit (real, re-verified, 2026-08-21)

Independent re-audit of all 4 `.agp-receipts/` rows in `~/xaas`, per-row artifact check (not
just the receipt-guard's own claim):

1. **`Operations-ash.gen.domain`** — receipt claims done; real artifact `lib/xaas/operations.ex`
   confirmed present. **Verified good.**
2. **`CapabilityLivenessReceipt-ash.gen.resource`** — receipt claims done; real artifact
   `lib/xaas/operations/capability_liveness_receipt.ex` confirmed present. **Verified good.**
3. **`CapabilityLivenessReceipt-ash.extend`** — receipt claims done; real `AshGraphql`
   reference confirmed present in the resource file. **Verified good.**
4. **`CapabilityLivenessReceipt-ash_postgres.generate_migrations`** — receipt claims done
   ("target: ... mix args: --name add_capability_liveness_receipt"); **re-confirmed false
   positive**, same gap first found 2026-08-20. Fresh evidence this pass: the only migration
   file matching this resource on disk,
   `priv/repo/migrations/20260820212909_add_capability_liveness_receipts.exs`, is a real,
   git-committed file (commit `3b32f74`, authored 2026-08-20 14:29) — timestamped **before**
   this receipt's own invocation, and named differently (plural `receipts`, not the
   `add_capability_liveness_receipt` name the receipted command actually requested). It is a
   pre-existing, unrelated migration from earlier legitimate work, not output of the receipted
   `ash_postgres.generate_migrations` call. No file matching what that specific invocation
   claimed to produce exists anywhere in the tree.

Also confirmed this pass: re-running `ggen sync` a further time reproduces 4/4 skip with
byte-identical receipt file contents (md5 before/after match exactly) — the *receipt
mechanism's* idempotency (same guard fires the same way every time) is solid; it is
specifically the *migration task's correctness* (receipt not implying real completed work)
that remains a known, now twice-confirmed gap, not a one-off fluke from the original run.

## Marketplace-wide `agp:rank`-style fan-out adoption catalog (real, 2026-08-21)

Scanned every `*.tmpl` file under both `~/ggen-marketplace/packs/` and `~/chatman-ecosystem/
platform-console/services/ggen-marketplace/ggen-packs-src/` (~200 packs total) for the
`for_each` SPARQL + `sh_after`/`sh_before` external-command-dispatch shape this pack's
`agp:rank` ordering applies to.

**Real result: this pack is currently the only one with that shape.** Neither
`ash-autofde-lab-connector-pack` nor `ash-subproject-pack-generator` (its closest siblings,
both also `for_each`-driven) use `sh_after`/`sh_before` — both generate files directly via
`to:` output paths, with no external command dispatch to order. Every other `for_each` match
across the ~200-pack sweep (mostly `shadcn`/UI component-scaffolding packs) is unrelated
file-fan-out with no command-ordering concern at all.

**Migration list: empty, honestly.** There is no other pack to migrate to `agp:rank`-style
ordering today — the shape hasn't spread beyond its origin pack yet. This is a real, checked
negative result, not an unexplored gap: worth revisiting if/when a second pack adopts the
`sh_after` external-command-dispatch pattern (the `ash-autofde-lab-connector-pack`'s `cnv-deploy`
`/invoke` call is the closest candidate architecturally, per this session's earlier `agp:`/`aac:`
vocabulary-unification discussion, but it currently dispatches via a template-embedded HTTP call
in the generated Elixir code, not via `sh_after`, so it doesn't share this specific shape either).
