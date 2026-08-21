# ash-igniter-gen-pipeline-pack: Ordered Task-Graph Fan-Out + examples/ + playground/

Status: approved for implementation planning
Date: 2026-08-20
Pack: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-igniter-gen-pipeline-pack/`
Proven consumer project: `~/xaas`

## Problem

The pack today proves one real, generalized mechanism: an `agp:CodegenTarget` row drives
a real Igniter-backed `mix` task via a templated `sh_after`, guarded `unless_exists`,
logged to `.agp-receipts/`. Verified for 2 distinct real `mixTask` values
(`ash.gen.resource`, `ash_postgres.generate_migrations`) against 1 real project (`~/xaas`).

Two real gaps block calling this "the combinatorial maximum of ggen+Ash integration":

1. **No ordering.** The SPARQL `for_each` query returns rows in whatever order the store
   gives them. This is safe only when every row is independent. Real Ash codegen has real
   dependency order — `ash.gen.domain` must run before `ash.gen.resource` for that domain,
   which must run before `ash.extend`/`ash_postgres.generate_migrations` for that
   resource. Nothing today encodes or enforces that order.
2. **No validation surface.** There is no place to exercise the pack's SPARQL query,
   template, and gate against small, deliberately-crafted fact sets without touching
   `~/xaas` (the only real consuming project) or writing throwaway files outside the
   pack. Anyone extending the vocabulary has to test against the one real project or not
   at all.

## Scope

In scope:
- `agp:rank` property + `ORDER BY ?rank` in the template's SPARQL query.
- Gate update to require `agp:rank` on every `agp:CodegenTarget`.
- `examples/` directory: small, self-contained ontology fact sets demonstrating ordered
  multi-category fan-out (domain → resource → extend → migrate), runnable independently
  of `~/xaas`.
- `playground/` directory: a minimal, disposable `ggen.toml` + vendored template/gate
  setup that lets someone run `ggen sync` against an `examples/` fact set in isolation,
  inspect the receipt log, and confirm ordering + idempotency — without needing a real
  compiling Ash/Igniter project.
- Real fan-out proof against `~/xaas`: populate real multi-rank rows, run real `ggen
  sync`, capture real receipts, confirm order and idempotency, update
  `MATURITY-MATRIX.md` / `MIX-TASKS-USAGE-GUIDE.md` with only what was actually verified.

Out of scope (explicitly deferred, not silently dropped):
- Solver-computed/inferred topological order — `agp:rank` is asserted by whoever writes
  the ontology facts, same authorship model the pack already uses.
- Ash→ontology reflection (reverse direction).
- A second real consuming project beyond `~/xaas`.
- ash_swarm resurrection as a standalone project (explicitly rejected this session —
  ash_swarm was a half-finished sketch; its `gen.reactor`/`gen.igniter_task` mix tasks
  are not part of this work).

## Design

### 1. Ontology change (`ontology.ttl`)

Add one new datatype property:

```turtle
agp:rank a owl:DatatypeProperty ; rdfs:domain agp:CodegenTarget ; rdfs:range xsd:integer ;
  rdfs:comment "Real, asserted topological position for ordered sh_after execution -- e.g. 0 for a domain, 1 for a resource depending on it, 2 for an extend, 3 for a migration. Asserted by whoever writes the ontology facts; this pack does not compute or infer it." .
```

### 2. Template change (`templates/ash_igniter_codegen.tmpl`)

SPARQL query gains `?rank` in `SELECT`, an unconditional (non-`OPTIONAL`) triple pattern
for `agp:rank`, and `ORDER BY ?rank`. `sh_after` and receipt-log body are unchanged —
only row order changes.

### 3. Gate change (`gates/010_required.rq`)

Add a third `UNION` branch flagging any `agp:CodegenTarget` missing `agp:rank`, matching
the existing pattern for `moduleName`/`domainModule`/`mixTask`.

### 4. `examples/` (new)

Small, numbered example fact sets, each a standalone `.ttl` file plus a short `README.md`
explaining what it demonstrates:

- `examples/01-single-domain-resource.ttl` — rank 0 domain, rank 1 resource depending on
  it. Smallest possible ordered case.
- `examples/02-full-chain.ttl` — rank 0 domain → rank 1 resource → rank 2 extend → rank 3
  migration, one full real chain.
- `examples/03-fan-out.ttl` — one rank-0 domain, N≥5 rank-1 resources depending on it,
  proving fan-out and ordering together (not just ordering in the abstract, per the
  approved design).

These are ontology fact fixtures only — no mix commands are expected to succeed against
them outside a real Ash project; their purpose is proving SPARQL ordering and gate
correctness, not real Igniter execution. That distinction is stated explicitly in
`examples/README.md`.

### 5. `playground/` (new)

A disposable, git-ignored-output scratch harness:

- `playground/ggen.toml` — points `[ontology] source` at one of the `examples/*.ttl`
  files (swappable), `[templates] dir` at the pack's own `templates/` (relative
  reference, honoring the documented "ontology must live inside the consuming project,
  no path traversal outside project root" ggen constraint — `playground/` *is* the
  project root for this purpose).
- `playground/README.md` — real, copy-pasteable instructions: `cd playground && ggen
  sync`, then inspect `.agp-receipts/*.mix.log` for the real command lines ggen would
  have run, in the order they'd run, without needing a real Elixir/Ash/Igniter
  installation (the `sh_after` commands will fail if `mix` / the target modules don't
  exist — that's expected and documented, not hidden; the playground validates
  ontology→command generation and ordering, not real Igniter side effects).
- `.gitignore` inside `playground/` for `.agp-receipts/` and any ggen cache dirs, so
  running the playground never accumulates untracked cruft into the pack's own git
  history.

### 6. Real fan-out proof against `~/xaas`

After 1–5 are in place and self-consistent (playground run confirms ordering), do the
real thing: add real `agp:rank`-carrying rows to `~/xaas/ontology.ttl` spanning at least
domain/resource/extend/migrate categories, run real `ggen sync`, capture the real receipt
log and `.mix.log` files, confirm:
- Domain generation's receipt file timestamp precedes dependent resources' (order proof).
- A second `ggen sync` run is 100% skip (idempotency preserved under the new query shape).
Then update `MATURITY-MATRIX.md` (new real data point, Generalization axis) and
`MIX-TASKS-USAGE-GUIDE.md` (document the ordering mechanism) with only this real
evidence — no scores move without a cited real run backing them, per this pack's
existing documentation-honesty standard.

## Testing / Verification

- Gate query (`gates/010_required.rq`) exercised against each `examples/*.ttl` file: rows
  with missing `agp:rank` must be flagged; complete rows must pass.
- `playground/` run against each `examples/*.ttl` file: confirm the rendered `sh_after`
  command sequence in `.agp-receipts/*.mix.log` matches the intended rank order for that
  example.
- Real `~/xaas` run: real receipts, real idempotency re-run, as described in step 6 above.
- No claim in `MATURITY-MATRIX.md`/`MIX-TASKS-USAGE-GUIDE.md` is edited without a
  concrete run backing it (dates, file paths, receipt contents cited), consistent with
  the pack's existing standard.

## Open questions / risks

- Whether `ggen sync`'s `for_each` actually executes `sh_after` calls in SPARQL result
  row order (vs. some other internal ordering) is asserted by this design but not yet
  confirmed against ggen's real engine behavior — the `playground/` step exists
  specifically to confirm or refute this before the real `~/xaas` run, cheaply.
- If ggen does *not* preserve `ORDER BY` result order through `for_each`, this design's
  core mechanism doesn't work as stated and needs revision (e.g. splitting into multiple
  rank-scoped templates executed in file order instead) — this must be checked early in
  implementation, not assumed.
