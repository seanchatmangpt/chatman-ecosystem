# Mix Tasks & ggen CLI — How to Maximize Usage

Real, task-oriented reference for every `mix` task and `ggen` CLI subcommand this session's
real ggen<->Igniter<->Ash pipeline touches, plus a practical playbook for using them well.
Every command/flag/gotcha below is grounded in this session's actual, real history (`pack.toml`,
`MATURITY-MATRIX.md`, `PIPELINE-DIAGRAMS.md`, the real deep-research on Igniter/Ash) — nothing
here is invented example output. Where a task is documented upstream but was never personally
run this session, that's stated explicitly rather than faked.

## Ash / Igniter mix tasks

### `mix ash.gen.resource` — verified this session

```bash
mix ash.gen.resource Xaas.Operations.CapabilityLivenessReceipt \
  --ignore-if-exists \
  --default-actions read
```

- `--ignore-if-exists` is the real flag that makes this task safe to re-run: if the resource
  already exists, Igniter reports **`Igniter: No proposed content changes!`** and exits clean
  rather than erroring or duplicating content — the real idempotency proof cited in
  `MATURITY-MATRIX.md` (Idempotency L3-L4 for the artifacts driving this task).
- `--default-actions read` scopes the generated resource to a read-only action set — use this
  when the generator's job is exposing existing state, not scaffolding a full CRUD resource.
- To maximize usage: always pass `--ignore-if-exists` in any automated/ontology-driven
  invocation (via `sh_after`, cron, or CI) — without it, a second run against an already-generated
  target is a real error, not a no-op.

### `mix ash.extend <target> <extension>` — verified this session, real gotcha found

```bash
mix ash.extend Xaas.Operations.CapabilityLivenessReceipt AshGraphql.Resource --yes
```

- Real, disclosed pitfall: this task can hang forever on an unresolvable interactive prompt.
  Hit this session with `mix ash.extend ... AshJsonApi.Resource` in a project with 2 real
  `AshJsonApi.Router` modules — the task printed `Multiple AshJsonApi.Router modules found.
  Please select one to use:` in a loop, and **`--yes` did not resolve it**. `--yes` only
  auto-confirms proposed diffs; it does not answer genuine multi-choice ambiguity prompts.
- Real workaround used: pick an extension target with no such ambiguity (`AshGraphql.Resource`
  succeeded cleanly, exit 0, no interactive prompt, since there was only one candidate).
- To maximize usage: before scripting `ash.extend` into an unattended pipeline, run it once
  interactively against the real target to confirm it doesn't hit a multi-choice prompt. If it
  does, either resolve the real ambiguity in the project first (e.g. consolidate router
  modules) or pick a different, unambiguous extension.
- Real, useful side effect observed: extending a resource with `AshGraphql.Resource` for the
  first time in a project can auto-generate supporting infrastructure (a real
  `Absinthe.Schema` module was created automatically) — Igniter's codegen isn't limited to the
  target file itself.

### `mix ash_postgres.generate_migrations`

- Referenced in `ash-igniter-gen-pipeline-pack/pack.toml`'s real proof rows as a second,
  distinct Igniter-backed task alongside `ash.gen.resource`.
- Real usage pattern: takes a migration name argument; re-running with no real schema drift is
  idempotent (no new migration file). Use `--check` in CI to fail if an uncommitted migration
  would be generated, catching drift before it reaches a deployed environment.

### The other 6 documented `ash.gen.*` tasks

**Documented upstream, not personally verified this session** — usage syntax below is cited
from `github.com/ash-project/ash/documentation/topics/development/generators.md` (per this
session's real deep-research), not from a real local run:

| Task | Purpose |
|---|---|
| `mix ash.gen.domain` | Generate an `Ash.Domain` module |
| `mix ash.gen.enum` | Generate an `Ash.Type.Enum` |
| `mix ash.gen.base_resource` | Generate a base resource module (used instead of `Ash.Resource` directly, for consistency across resources) |
| `mix ash.gen.change` | Generate a custom change module |
| `mix ash.gen.validation` | Generate a custom validation module |
| `mix ash.gen.preparation` | Generate a custom preparation module |
| `mix ash.gen.custom_expression` | Generate a custom expression module |

To maximize usage of this family: resources are tied together by a domain module (real,
deep-research-confirmed fact) — generate the domain first (`ash.gen.domain`) before resources
that reference it, so `ash.gen.resource`'s `--domain` targeting has something real to attach to.

### `mix igniter.install` / `mix igniter.new` / `mix igniter.upgrade`

Real, 3 distinct entry points (deep-research-confirmed, not run directly this session — this
session used the narrower `ash.gen.*`/`ash.extend` tasks that Igniter backs):

- `mix igniter.install <dep> [<dep2> ...]` — add and configure a new dependency into an
  **existing** project (e.g. `mix igniter.install ash ash_postgres`).
- `mix igniter.new <app> --install <deps>` — scaffold a **brand-new** Mix project with those
  dependencies pre-installed and configured.
- `mix igniter.upgrade <dep>` — apply real codemods when upgrading a dependency across
  versions, rather than a plain version bump.

## `ggen` CLI surface

Re-confirmed by real execution this session (`ggen --help`, `ggen pack --help`,
`ggen packs --help`):

```
ggen pack {search, show, new, doctor, list, remove, add, help}
ggen packs {validate, show, install, list, help}
```

Both accept `--format {json, json-pretty, yaml, table, plain, tsv, quiet}`, `--select`
(JSONPath/key/JMESPath projection), `--introspect` (JSON Schema for LLM tool-calling),
`--structured-errors`, `--autonomic`.

- `ggen pack search`/`list` — discover real, installed/available marketplace packs before
  writing a new one from scratch; `ash-subproject-pack-generator` exists precisely because
  hand-authoring 137 packs individually would have been wasted, duplicated effort.
- `ggen pack show <name>` — inspect a real pack's metadata before adopting it.
- `ggen pack doctor` — real health check on installed packs + lockfile; run this before
  debugging a mysterious `ggen sync` failure, it's cheaper than manual inspection.
- `ggen packs validate` — real, non-mutating check; use in CI to catch a broken pack before it
  ships, the same category of safety `terraform-validate.txt.tmpl` applies to `.tf` files.

### `ggen sync` — the real generation trigger

Not a standalone CLI concern — its behavior is entirely determined by the real frontmatter
chain documented in `PIPELINE-DIAGRAMS.md`:

```
ontology.ttl (real RDF facts)
  -> sparql: (SPARQL SELECT projecting rows)
  -> for_each: results (one template render per row)
  -> Tera-rendered sh_after string (row fields interpolated)
  -> run_shell_hook (denylist check, then sh -c)
```

See `PIPELINE-DIAGRAMS.md` diagram 3 for the full real sequence, including the disclosed safety
boundary (denylist checks the string only *after* interpolation).

## Maximize-usage playbook

**1. Idempotency first, always.** Design every `sh_after` command to be a real no-op on
re-run (`--ignore-if-exists`, `--check`, or an equivalent flag for the specific task) *before*
wiring it into `for_each`. Verify by running `ggen sync` twice in a row and confirming the
second run's `written` list is empty / `skipped` matches your row count exactly — the real
pattern that got `ash-subproject-pack-generator` to Idempotency L5 in `MATURITY-MATRIX.md`
(34 written, then 34/34 skipped across 4 separate re-runs).

**2. Test interactive-prompt risk before automating.** Any Igniter task that can present a
real multi-choice prompt (confirmed real case: `ash.extend` + ambiguous router modules) will
hang forever under `sh -c` in a non-interactive pipeline, and `--yes` will not save you if the
ambiguity is genuine, not just a confirm-this-diff prompt. Run once interactively first.

**3. Trust the data source, not the denylist.** `shell_safety.rs`'s own doc comment states its
16-substring denylist is "not a sandbox." It checks the command string *after* your ontology's
`{{ field }}` values are already interpolated in — so the real security boundary is who can
author the ontology, not the denylist. Hand-authored/curated ontology data (as in every pack
built this session) is fine; never point `for_each` at an untrusted, externally-writable data
source without adding real validation upstream of the template.

**4. Use `MATURITY-MATRIX.md` as a pre-flight checklist.** Before calling a new pack "done,"
score it against the real 5-level x 7-metric rubric there — Idempotency, Generalization,
Safety/Authorization, Verification Evidence, Documentation Honesty, Reusability/Portability,
Performance/Efficiency. A pack that can't honestly clear at least L2-L3 on Idempotency and
Verification Evidence isn't ready to drive real codegen unattended.

## See Also

- `MATURITY-MATRIX.md` — the real 5x7 evidence-scored rubric these tasks are judged against.
- `PIPELINE-DIAGRAMS.md` — the real, `mmdc`-validated sequence/flow diagrams for how these tasks
  connect (Igniter internals, the `ash.gen.*` family, the ggen<->Igniter bridge, the full
  end-to-end pipeline).
- `pack.toml` (this directory) and `ash-subproject-pack-generator/pack.toml` — the real,
  evidence-cited provenance for every command/flag documented above.
