# Ash-Igniter-Gen Task-Graph Fan-Out Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ordered (`agp:rank`) multi-category fan-out to `ash-igniter-gen-pipeline-pack`, with an `examples/` fixture set and a `playground/` harness to validate ordering and gate behavior in isolation, then prove it for real against `~/xaas`.

**Architecture:** One new ontology property (`agp:rank`) threaded through the existing SPARQL `for_each` template (`ORDER BY ?rank`) and its gate. `examples/` holds standalone `.ttl` fixtures. `playground/` is a disposable, self-contained ggen project (its own vendored copy of the template/gate, per the pack's documented "ontology/templates must live inside the consuming project, no path traversal outside project root" constraint) used to run `ggen sync` against an example fixture and inspect ordering before touching the real `~/xaas` project.

**Tech Stack:** Turtle/RDF (ontology), SPARQL (gate + template query), ggen CLI (`ggen sync`), `mix` (real Igniter-backed tasks, real project only).

**Spec:** `docs/superpowers/specs/2026-08-20-ash-igniter-gen-task-graph-design.md`

## Global Constraints

- Every `agp:CodegenTarget` must have `agp:moduleName`, `agp:domainModule`, `agp:mixTask`, and (after this plan) `agp:rank` — gate-enforced, matching the pack's existing required-property pattern.
- `agp:mixArgs` remains real-optional (`OPTIONAL` in SPARQL) — do not make it required.
- `agp:rank` is asserted by whoever writes the ontology facts, never computed/inferred by this pack.
- ggen refuses ontology/template paths outside the project root (documented, confirmed constraint in `~/xaas/ggen.toml`'s comments) — `playground/` must vendor its own copies, not reference `../templates` or `../examples` via `ggen.toml` paths.
- No claim in `MATURITY-MATRIX.md` / `MIX-TASKS-USAGE-GUIDE.md` may be edited without a concrete, cited real run backing it (dates, file paths, receipt contents) — this is the pack's existing documentation-honesty standard, not new for this plan.
- Pack root for all relative paths below: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/` inside the `chatman-ecosystem` repo.

---

## Task 1: Add `agp:rank` to the ontology

**Files:**
- Modify: `ontology.ttl`

**Interfaces:**
- Produces: `agp:rank` — `owl:DatatypeProperty`, domain `agp:CodegenTarget`, range `xsd:integer`. Later tasks' SPARQL queries reference it by this exact IRI (`agp:rank`, prefix `agp:` = `<https://ggen.io/ontology/ash-igniter-gen-pipeline#>`).

- [ ] **Step 1: Add the property definition**

Append to `ontology.ttl`, immediately after the existing `agp:mixArgs` block:

```turtle
agp:rank a owl:DatatypeProperty ; rdfs:domain agp:CodegenTarget ; rdfs:range xsd:integer ;
  rdfs:comment "Real, asserted topological position for ordered sh_after execution -- e.g. 0 for a domain, 1 for a resource depending on it, 2 for an extend, 3 for a migration. Asserted by whoever writes the ontology facts; this pack does not compute or infer it." .
```

- [ ] **Step 2: Verify the file is valid Turtle**

Run: `ggen pack doctor` from the pack root (this is the pack's own real validation entry point; if unavailable, at minimum confirm the file has no unbalanced `;`/`.` by eye-diffing against the existing property blocks' punctuation pattern).
Expected: no syntax errors reported.

- [ ] **Step 3: Commit**

```bash
cd platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack
git add ontology.ttl
git commit -m "ash-igniter-gen-pipeline-pack: add agp:rank property for ordered fan-out"
```

---

## Task 2: Order the template's SPARQL query by rank

**Files:**
- Modify: `templates/ash_igniter_codegen.tmpl`

**Interfaces:**
- Consumes: `agp:rank` from Task 1.
- Produces: template's `sh_after` calls now execute in ascending `?rank` order (assuming ggen preserves SPARQL result order through `for_each` — this exact assumption is checked in Task 5, not here).

- [ ] **Step 1: Update the SPARQL query block**

Replace the `sparql:` block in `templates/ash_igniter_codegen.tmpl` with:

```yaml
sparql:
  results: |
    PREFIX agp: <https://ggen.io/ontology/ash-igniter-gen-pipeline#>
    SELECT ?moduleName ?domainModule ?mixTask ?mixArgs ?rank WHERE {
      ?t a agp:CodegenTarget ;
         agp:moduleName ?moduleName ;
         agp:domainModule ?domainModule ;
         agp:mixTask ?mixTask ;
         agp:rank ?rank .
      OPTIONAL { ?t agp:mixArgs ?mixArgs . }
    }
    ORDER BY ?rank
```

Leave the frontmatter's `to:`, `skip_empty`, `unless_exists`, `for_each`, and `sh_after` lines, and the template body below the frontmatter, unchanged — this task only changes row order and adds the required `?rank` binding.

- [ ] **Step 2: Confirm the file parses**

Run: `ggen pack doctor` from the pack root (or `ggen pack show ash-igniter-gen-pipeline-pack` if `doctor` requires a registered pack).
Expected: template frontmatter/YAML parses without error.

- [ ] **Step 3: Commit**

```bash
git add templates/ash_igniter_codegen.tmpl
git commit -m "ash-igniter-gen-pipeline-pack: order sh_after execution by agp:rank"
```

---

## Task 3: Gate `agp:rank` as required

**Files:**
- Modify: `gates/010_required.rq`

**Interfaces:**
- Consumes: `agp:rank` from Task 1.
- Produces: gate now flags any `agp:CodegenTarget` missing `agp:rank`, alongside the existing three required properties.

- [ ] **Step 1: Add a fourth UNION branch**

Replace `gates/010_required.rq`'s body with:

```sparql
# MESSAGE: every agp:CodegenTarget must have a non-empty agp:moduleName,
# agp:domainModule, agp:mixTask, and agp:rank -- the template interpolates
# the first three unconditionally and orders execution by the fourth
# (mixArgs is real-optional, deliberately not gated). A row missing any of
# these can't drive a real, correctly-ordered mix command line. Any row
# returned here = a subject missing its required property.
PREFIX agp: <https://ggen.io/ontology/ash-igniter-gen-pipeline#>
SELECT ?s ?missing WHERE {
  {
    ?s a agp:CodegenTarget . BIND(agp:moduleName AS ?missing)
  } UNION {
    ?s a agp:CodegenTarget . BIND(agp:domainModule AS ?missing)
  } UNION {
    ?s a agp:CodegenTarget . BIND(agp:mixTask AS ?missing)
  } UNION {
    ?s a agp:CodegenTarget . BIND(agp:rank AS ?missing)
  }
  FILTER NOT EXISTS { ?s ?missing ?any }
}
ORDER BY ?s ?missing
```

- [ ] **Step 2: Sanity-check against the current (soon-to-be-fixed) ontology**

Run: `ggen pack doctor` from the pack root, or manually run the query against `ontology.ttl` via whatever SPARQL-runner the pack's `gates` mechanism uses (check `pack.toml`/`ggen.toml` for the gate invocation command if unclear).
Expected: zero rows returned — every existing `agp:CodegenTarget` in `ontology.ttl` (there are none committed yet at pack level; this really validates against `~/xaas`'s vendored copy once Task 7 updates it, so at this point in the plan a clean pack-level ontology with no `CodegenTarget` individuals yet is expected to return zero rows trivially).

- [ ] **Step 3: Commit**

```bash
git add gates/010_required.rq
git commit -m "ash-igniter-gen-pipeline-pack: gate agp:rank as required"
```

---

## Task 4: `examples/` fixtures

**Files:**
- Create: `examples/README.md`
- Create: `examples/01-single-domain-resource.ttl`
- Create: `examples/02-full-chain.ttl`
- Create: `examples/03-fan-out.ttl`

**Interfaces:**
- Consumes: `agp:CodegenTarget`, `agp:moduleName`, `agp:domainModule`, `agp:mixTask`, `agp:mixArgs`, `agp:rank` (Task 1).
- Produces: fixture files consumed by Task 5 (`playground/`) and Task 6 (validation run).

- [ ] **Step 1: Write `examples/README.md`**

```markdown
# examples/

Standalone ontology fact fixtures for `ash-igniter-gen-pipeline-pack`. These are ontology
fact fixtures only -- no `mix` command is expected to succeed against them outside a real
Ash/Igniter project. Their purpose is proving SPARQL row ordering (`agp:rank`) and gate
correctness, not real Igniter execution.

Use with `../playground/` (see its README) to run a real `ggen sync` and inspect the
rendered `sh_after` command order in `.agp-receipts/*.mix.log`.

| File | Demonstrates |
|---|---|
| `01-single-domain-resource.ttl` | Smallest ordered case: one rank-0 domain, one rank-1 resource depending on it. |
| `02-full-chain.ttl` | Full real chain: rank 0 domain -> rank 1 resource -> rank 2 extend -> rank 3 migration. |
| `03-fan-out.ttl` | One rank-0 domain, 5 rank-1 resources depending on it -- fan-out and ordering together. |
```

- [ ] **Step 2: Write `examples/01-single-domain-resource.ttl`**

```turtle
@prefix agp: <https://ggen.io/ontology/ash-igniter-gen-pipeline#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

agp:ExampleDomain a agp:CodegenTarget ;
  agp:moduleName "Operations" ;
  agp:domainModule "Example" ;
  agp:mixTask "ash.gen.domain" ;
  agp:rank 0 .

agp:ExampleWidgetResource a agp:CodegenTarget ;
  agp:moduleName "Widget" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .
```

- [ ] **Step 3: Write `examples/02-full-chain.ttl`**

```turtle
@prefix agp: <https://ggen.io/ontology/ash-igniter-gen-pipeline#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

agp:ChainDomain a agp:CodegenTarget ;
  agp:moduleName "Operations" ;
  agp:domainModule "Example" ;
  agp:mixTask "ash.gen.domain" ;
  agp:rank 0 .

agp:ChainWidgetResource a agp:CodegenTarget ;
  agp:moduleName "Widget" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .

agp:ChainWidgetExtend a agp:CodegenTarget ;
  agp:moduleName "Widget" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.extend" ;
  agp:mixArgs "AshGraphql.Resource --yes" ;
  agp:rank 2 .

agp:ChainWidgetMigration a agp:CodegenTarget ;
  agp:moduleName "Widget" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash_postgres.generate_migrations" ;
  agp:mixArgs "--name add_widget" ;
  agp:rank 3 .
```

- [ ] **Step 4: Write `examples/03-fan-out.ttl`**

```turtle
@prefix agp: <https://ggen.io/ontology/ash-igniter-gen-pipeline#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

agp:FanOutDomain a agp:CodegenTarget ;
  agp:moduleName "Operations" ;
  agp:domainModule "Example" ;
  agp:mixTask "ash.gen.domain" ;
  agp:rank 0 .

agp:FanOutResourceA a agp:CodegenTarget ;
  agp:moduleName "Alpha" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .

agp:FanOutResourceB a agp:CodegenTarget ;
  agp:moduleName "Bravo" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .

agp:FanOutResourceC a agp:CodegenTarget ;
  agp:moduleName "Charlie" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .

agp:FanOutResourceD a agp:CodegenTarget ;
  agp:moduleName "Delta" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .

agp:FanOutResourceE a agp:CodegenTarget ;
  agp:moduleName "Echo" ;
  agp:domainModule "Example.Operations" ;
  agp:mixTask "ash.gen.resource" ;
  agp:mixArgs "--ignore-if-exists --default-actions read" ;
  agp:rank 1 .
```

- [ ] **Step 5: Verify all three files gate-clean**

For each file, confirm every `agp:CodegenTarget` individual has `moduleName`, `domainModule`, `mixTask`, `rank` — visually diff each block above against `gates/010_required.rq`'s four required properties. All five individuals in `03-fan-out.ttl` and all blocks in the other two files satisfy this by construction above.

- [ ] **Step 6: Commit**

```bash
git add examples/
git commit -m "ash-igniter-gen-pipeline-pack: add examples/ ordering fixtures"
```

---

## Task 5: `playground/` harness

**Files:**
- Create: `playground/ggen.toml`
- Create: `playground/templates/ash_igniter_codegen.tmpl`
- Create: `playground/gates/010_required.rq`
- Create: `playground/README.md`
- Create: `playground/.gitignore`

**Interfaces:**
- Consumes: `templates/ash_igniter_codegen.tmpl` (Task 2), `gates/010_required.rq` (Task 3) — vendored, not referenced, per the ggen path-root constraint.
- Produces: a runnable isolated ggen project at `playground/` for Task 6.

- [ ] **Step 1: Vendor the template**

Copy the exact post-Task-2 content of `templates/ash_igniter_codegen.tmpl` to `playground/templates/ash_igniter_codegen.tmpl` (same content, same path segment `templates/` relative to `playground/`).

```bash
mkdir -p playground/templates playground/gates
cp templates/ash_igniter_codegen.tmpl playground/templates/ash_igniter_codegen.tmpl
cp gates/010_required.rq playground/gates/010_required.rq
```

- [ ] **Step 2: Write `playground/ggen.toml`**

```toml
# Disposable playground project root for ash-igniter-gen-pipeline-pack.
# ontology.ttl is NOT committed -- copy an examples/*.ttl fixture into
# place before running `ggen sync` (see README.md). templates/ and
# gates/ here are vendored copies of the pack's own files (ggen refuses
# ontology/template paths outside the project root, so this project
# root cannot reference ../templates or ../examples directly).

[project]
name = "ash-igniter-gen-pipeline-playground"

[ontology]
source = "ontology.ttl"

[templates]
dir = "templates"
```

- [ ] **Step 3: Write `playground/README.md`**

```markdown
# playground/

Disposable, self-contained ggen project for validating
`ash-igniter-gen-pipeline-pack`'s ordering and gate behavior in isolation, without
touching the real `~/xaas` project.

## Usage

```bash
cd platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/playground
cp ../examples/02-full-chain.ttl ontology.ttl
ggen sync
```

Then inspect `.agp-receipts/*.mix.log` -- the file *modification order* (or, if `ggen sync`
prints its own per-row log, the printed order) should match ascending `agp:rank`: the
domain row first, then the resource, then the extend, then the migration.

The `sh_after mix ...` commands **will fail** here (no real Elixir/Ash/Igniter project
exists in `playground/`) -- that's expected. This harness validates ontology-to-command
generation and row ordering, not real Igniter side effects; real side effects are only
ever validated against `~/xaas` (see the pack's `MATURITY-MATRIX.md`).

`ontology.ttl`, `.agp-receipts/`, and ggen's own cache/state directories are gitignored --
swap in a different `examples/*.ttl` file and re-run freely; nothing here should ever need
a commit.
```

- [ ] **Step 4: Write `playground/.gitignore`**

```
ontology.ttl
.agp-receipts/
.ggen-v2/
```

- [ ] **Step 5: Commit**

```bash
git add playground/
git commit -m "ash-igniter-gen-pipeline-pack: add playground/ validation harness"
```

---

## Task 6: Validate ordering assumption in `playground/`

**Files:**
- None created/modified — this task is a verification run. It may produce a fix to Task 2 if the core assumption is wrong (see Step 3's fallback).

**Interfaces:**
- Consumes: `playground/` (Task 5), `examples/02-full-chain.ttl` (Task 4).
- Produces: confirmation (or refutation) of this plan's core assumption — that ggen's `for_each` executes `sh_after` in SPARQL `ORDER BY` result order — gating whether Task 7 can proceed as designed.

- [ ] **Step 1: Run the playground against the full-chain example**

```bash
cd platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/playground
cp ../examples/02-full-chain.ttl ontology.ttl
rm -rf .agp-receipts .ggen-v2
ggen sync
```

- [ ] **Step 2: Inspect receipt order**

```bash
ls -la .agp-receipts/*.mix.log
```

Expected: four files, one per row in `02-full-chain.ttl`. Compare their creation/modification
timestamps (`ls -la` order, or `stat` per file) against the intended rank order: `Operations`
(domain, rank 0) → `Widget`+`ash.gen.resource` (rank 1) → `Widget`+`ash.extend` (rank 2) →
`Widget`+`ash_postgres.generate_migrations` (rank 3).

- [ ] **Step 3: Resolve the open question from the spec**

If timestamps confirm ascending-rank order: the core mechanism works as designed. Proceed to
Task 7 as written.

If timestamps do **not** confirm ascending-rank order (ggen does not preserve `ORDER BY`
through `for_each`): stop here. This is a real design assumption failure per the spec's
"Open questions / risks" section — do not proceed to Task 7. Instead, this plan's Task 2
needs revision to an alternative mechanism (e.g., splitting `templates/ash_igniter_codegen.tmpl`
into four rank-scoped template files executed in filename order, `templates/00-domain.tmpl`,
`templates/01-resource.tmpl`, etc.) — surface this finding and get explicit sign-off on the
revised approach before continuing, rather than silently reworking the plan.

- [ ] **Step 4: Clean up playground state**

```bash
rm -f ontology.ttl
rm -rf .agp-receipts .ggen-v2
```

(No commit — `playground/`'s working files are gitignored per Task 5; this step just leaves
the harness clean for the next person.)

---

## Task 7: Real fan-out proof against `~/xaas`

**Files:**
- Modify: `~/xaas/ontology.ttl`
- Modify: `MATURITY-MATRIX.md` (in the pack root)
- Modify: `MIX-TASKS-USAGE-GUIDE.md` (in the pack root)

**Interfaces:**
- Consumes: confirmed-working `agp:rank` mechanism from Task 6.
- Produces: real, cited evidence of ordered multi-category fan-out against the pack's one real consuming project.

**Precondition:** Task 6 confirmed the ordering mechanism works as designed. If Task 6 required a design revision, redo Tasks 1–3 per the revised mechanism before starting this task.

- [ ] **Step 1: Re-vendor the updated template/gate into `~/xaas`**

`~/xaas`'s `ggen.toml` comments state its ontology is a vendored copy, kept in sync manually.
Copy this pack's post-Task-1/2/3 `ontology.ttl`'s new `agp:rank` property block and the
updated template/gate into `~/xaas`'s equivalent vendored locations (check `~/xaas/ggen.toml`'s
`[templates] dir` value for the exact target path — per the file read during design, this is
`templates-hooks/`).

```bash
# From the pack root:
grep -A2 "agp:rank" ontology.ttl
```

Manually merge that property block into `~/xaas/ontology.ttl`'s vendored ontology header
section (alongside the existing `agp:mixTask`/`agp:mixArgs` properties it already vendors),
and copy the updated `templates/ash_igniter_codegen.tmpl` content into
`~/xaas/templates-hooks/` under its existing equivalent filename.

- [ ] **Step 2: Add real `agp:rank`-carrying rows to `~/xaas/ontology.ttl`**

Using `~/xaas`'s real domain/resource naming conventions (inspect existing `xar:RenderTarget`
individuals already in the file for real module/domain names to reuse or extend), add at
least one real row per rank 0–3 category: one real domain, one or more real resources
depending on it, one real `ash.extend` row, one real `ash_postgres.generate_migrations` row —
each as an `agp:CodegenTarget` individual with `agp:rank` set per its category, following the
exact property pattern shown in `examples/02-full-chain.ttl` (Task 4) but with real `~/xaas`
module/domain names instead of the `Example.*` placeholders.

- [ ] **Step 3: Run real `ggen sync` against `~/xaas`**

```bash
cd ~/xaas
ggen sync
```

Capture: full stdout/stderr, and the resulting `.agp-receipts/*.mix.log` files' real content
(the real `mix` command lines and their real output).

- [ ] **Step 4: Confirm ordering and idempotency**

Check the real receipt files' order/timestamps match ascending `agp:rank`, same method as
Task 6 Step 2. Then run `ggen sync` a second time and confirm 100% skip (no new/changed
receipt files) — the existing idempotency guarantee must still hold under the new
`ORDER BY`-augmented query.

- [ ] **Step 5: Update `MATURITY-MATRIX.md` with real evidence only**

Add a new dated entry (using this task's real run's actual date, receipt file paths, and
row/rank counts) to the Generalization axis discussion for `ash-igniter-gen-pipeline-pack`,
citing: how many distinct `agp:mixTask` values were exercised in this run, how many
`agp:CodegenTarget` rows, confirmation of rank-ordered execution, confirmation of idempotent
re-run. Do not adjust the level score without citing this real run as the reason, following
the file's existing citation style (see e.g. the "Performance/Efficiency Measurement Update"
section for the expected format: what was measured, real numbers, what score changed and why).

- [ ] **Step 6: Update `MIX-TASKS-USAGE-GUIDE.md` with the ordering mechanism**

Add a short real section documenting `agp:rank` and its `ORDER BY` mechanism, cross-referencing
this run's evidence, following the existing "verified this session" / "documented upstream,
not personally verified" honesty convention already used throughout that file.

- [ ] **Step 7: Commit**

```bash
cd ~/xaas
git add ontology.ttl templates-hooks/
git commit -m "xaas: add real agp:rank-ordered CodegenTarget rows (domain/resource/extend/migrate)"

cd - # back to chatman-ecosystem pack root
git add MATURITY-MATRIX.md MIX-TASKS-USAGE-GUIDE.md
git commit -m "ash-igniter-gen-pipeline-pack: document real ordered fan-out proof against ~/xaas"
```

---

## Self-Review Notes

- **Spec coverage:** Task 1 = spec §1 (ontology change). Task 2 = spec §2 (template change).
  Task 3 = spec §3 (gate change). Task 4 = spec §4 (`examples/`). Task 5 = spec §5
  (`playground/`). Task 6 = spec's "Open questions / risks" (explicitly checked, not assumed).
  Task 7 = spec §6 (real fan-out proof + doc updates). All in-scope spec sections have a task.
  Out-of-scope items (solver-computed order, reflection, second project, ash_swarm) are not
  tasked, matching the spec's explicit exclusions.
- **Placeholder scan:** no TBD/TODO; every code/config step above has literal file content, not
  a description of content.
- **Type/name consistency:** `agp:rank` (Task 1) is the exact IRI used unchanged through Tasks
  2, 3, 4, 6, 7. Template path `templates/ash_igniter_codegen.tmpl` and gate path
  `gates/010_required.rq` are consistent across Tasks 1–2, 3, and their vendored copies in
  Task 5. `playground/ggen.toml`'s `[templates] dir = "templates"` matches the vendored copy's
  actual location created in Task 5 Step 1.
