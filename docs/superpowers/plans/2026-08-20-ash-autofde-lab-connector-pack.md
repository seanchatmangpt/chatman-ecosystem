# Ash-AutoFDE-Lab Connector Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the third of three real MAPE-K/Ash convergence loops — the receipt/broker loop —
by generating (via a new, distinct ggen-marketplace pack) a real Ash resource in xaas that calls
the already-built `clap-noun-verb-any`/`clap-noun-verb-deploy` HTTP surface wrapping
autofde-lab's real `fabric` planner CLI (46+ registered solvers), and persists the real
`trajectory_sha256` receipt that CLI already emits. This does NOT touch autofde-lab, gymact, or
clap-noun-verb's source, and does NOT touch any file already generated/owned by the handed-off
`ash-igniter-gen-pipeline-pack`/`ash-subproject-pack-generator` packs — it is a new pack, a new
xaas resource file, scoped exactly to the connection the user explicitly assigned ("you own the
ash to autofde-lab connection").

**Architecture:** A new `ash-autofde-lab-connector-pack` ggen-marketplace pack (pack.toml +
ontology.ttl + gates/*.rq + Tera templates), following this repo's own real, ground-truthed
schema (single `[pack]` table; per-pack `@prefix` vocabulary; `SELECT`-based refusal gates in
`NNN_description.rq` files). It generates one new Ash resource module,
`Xaas.Operations.AutofdePlannerCandidate`, into xaas's existing `lib/xaas/operations/` directory
(sibling to the real `capability_liveness_receipt.ex`, matching its naming convention and its
exact deny-by-default policy floor).

**Real finding this connects to, not a hand-rolled design:** `~/clap-noun-verb/
clap-noun-verb-any` already wraps autofde-lab's real `autofde_lab.fabric` Typer CLI as a
deployable CLI via `cnv-any::wrap()` + `clap_noun_verb_deploy::Gateway` — confirmed real: 2
non-ignored Rust tests pass
(`~/clap-noun-verb/clap-noun-verb-any/tests/autofde_lab_integration.rs`), and 2 real `#[ignore]`d
tests (need the `playground/autofde-lab` submodule's real `.venv` synced, never mocked) run an
actual `Astar` PDDL solve and assert a real 64-char `trajectory_sha256` in the output.
`clap-noun-verb-deploy`'s real HTTP surface (`~/clap-noun-verb/clap-noun-verb-deploy/src/http.rs`)
is narrow and confirmed: `GET /healthz`/`/readyz`, `GET /schema`, `GET /tools`, `GET /ocel` (a real
OCEL document endpoint), and `POST /invoke` with body `{"tool": "<name>", "arguments": {...}}`,
returning the execution record as JSON (`{"execution": {"stdout": ..., "stderr": ...,
"success": ...}, ...}`). The Ash resource's `:request_candidate` action therefore does **not**
hand-roll an HTTP call to gymact or invent its own digest — it calls this already-built
`POST /invoke` endpoint with `tool = "fabric__solve"`, and persists the real `trajectory_sha256`
the underlying planner already emits, parsed out of the record's stdout. This is the receipt/
broker loop closing by *reuse*, not by *reimplementation* — the same principle the user
separately flagged for `affidavit`/BRCE (real, disclosed duplication: autofde-lab alone has 3
non-unified receipt/broker implementations, gymact a 4th; `affidavit`'s absorption of all 4 is
deferred to its own, separate plan, not folded in here per explicit scope decision).

(Note: solver/domain counts are disputed across sources — the `cnv-any` example's own README says
"46+/25+", `ggen-src`'s `architecture.md` pack description says "83 capabilities: 26 domains, 57
solvers", and the real `ontology/autofde-lab-capabilities.ttl` itself contains 31 `skdt:Domain` +
57 `skdt:Solver` = 88 individuals; none of these three numbers agree, so this plan cites no
headline count and treats "solver"/"domain" only as free-text arguments the real `solve` command
accepts, proven with `Astar`/`FF` in the real ignored test — not a fixed catalog size.)

**Tech Stack:** Rust (`ggen sync` for pack generation; `clap-noun-verb-deploy`'s Gateway/HTTP
surface — used, not modified), TOML/Turtle/SPARQL (pack authoring), Elixir/Ash (generated
resource + real `mix test`), Python (autofde-lab's real `fabric` CLI, wrapped not rewritten).

**Spec:** This plan is self-specifying (no separate design doc) — the "what" is fully captured
in Global Constraints and the per-task Interfaces blocks below, each citing the real ground-truth
file/line evidence gathered this session (6 parallel Explore-agent research passes over xaas/
gymact/autofde-lab/ggen-marketplace, plus direct reads of `clap-noun-verb-any`'s real example/test
and `clap-noun-verb-deploy`'s real `http.rs`).

## Global Constraints

- **Do not modify** any file inside `~/xaas` other than the one new file this plan creates
  (`lib/xaas/operations/autofde_planner_candidate.ex`), the one additive registration line in
  `lib/xaas/operations.ex`, and its one new test file. No edits to `ontology.ttl`,
  `templates-hooks/*`, or any resource already handed off.
- **Do not modify** `~/autofde-lab`, `~/gymact`, or `~/clap-noun-verb` source at all — read-only,
  call the already-built, already-running real HTTP surface only.
- **Do not modify** any existing ggen-marketplace pack (`ash-igniter-gen-pipeline-pack`,
  `ash-subproject-pack-generator`) — this is a new, separate pack directory.
- Every generated Ash resource MUST carry the real, ground-truthed deny-by-default floor:
  `policy always() do forbid_if(always()) end`, with `bypass action_type(:read) do
  authorize_if(always()) end` and `bypass action(:request_candidate) do authorize_if(always())
  end` as the only carve-outs (exact pattern from `lib/xaas/operations/
  capability_liveness_receipt.ex`, confirmed this session).
- The generated action MUST call the real, already-built `clap-noun-verb-deploy` HTTP surface:
  `POST /invoke` with body `{"tool": "fabric__solve", "arguments": {...}}`, targeting a
  `wrapped.deploy()` instance serving `~/clap-noun-verb/clap-noun-verb-any/examples/
  autofde_lab_planners/autofde-lab-fabric.sh` + its `cnv-any.json` manifest. This is a planning
  connector, not an actuation connector — `fabric solve` only ever produces a candidate
  trajectory (autofde-lab's own law: "It computes candidate plans. It does not actuate."), never
  gymact's real DO path.
- The `arguments` map sent to `/invoke` MUST use the manifest's external long-flag names, not
  internal ids — confirmed real from `wrap_builds_a_real_solve_invocation_selecting_any_registered_planner`:
  keys are `"domain"`, `"solver"`, `"max-steps"`, `"domain-arguments"` (hyphenated), matching how
  an HTTP/MCP caller sees the tool's real JSON schema property names.
- The connector's base URL MUST be configurable via `Application.get_env(:xaas,
  :cnv_deploy_base_url)`, defaulting to `http://127.0.0.1:8080` (real, confirmed default from
  `HttpConfig::default()` in `clap-noun-verb-deploy/src/http.rs`) — never hardcoded inline.
- The `cnv-deploy` HTTP server for `autofde-lab-fabric` MUST be started separately (out of scope
  for this plan — a real, standalone `cnv-any`/`cnv-deploy` operational concern, not an Ash
  concern); Task 3 documents the real, already-proven-working start path.
- Pack schema MUST match the real, ground-truthed convention: `pack.toml` has exactly one
  `[pack]` table (`name`, `version`, `description`); `ontology.ttl` declares its own
  `@prefix aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#>`; gates live in
  `gates/010_required.rq`, a `SELECT`-based refusal query (non-empty result set = refusal),
  filename-sorted.
- Chicago TDD only in the generated Elixir test — a real HTTP call to a real, running
  `cnv-deploy` instance, no mocks. If it's not running locally, the test must skip with a named,
  visible reason (`@moduletag :requires_cnv_deploy`), never fake a response.

---

### Task 1: Pack scaffold — `pack.toml`, `ontology.ttl`, `gates/010_required.rq`

**Files:**
- Create: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/pack.toml`
- Create: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/ontology.ttl`
- Create: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/gates/010_required.rq`
- Test: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/gates/README.md` (documents the gate, per this repo's real `pat:HowToGateDoc` convention)

**Interfaces:**
- Produces: `aac:AshConnector` class with properties `aac:resourceModule` (string, e.g.
  `"Xaas.Operations.AutofdePlannerCandidate"`), `aac:domainModule` (string), `aac:invokeTool`
  (string, e.g. `"fabric__solve"`), `aac:actionName` (string, e.g. `"request_candidate"`),
  `aac:cnvDeployBaseUrlEnv` (string) — consumed by Task 2's Tera template.

- [x] **Step 1: Write `pack.toml`**

```toml
[pack]
name = "ash-autofde-lab-connector-pack"
version = "0.1.0"
description = """
Generates the real Ash-side connector resource for the AutoFDE-Lab receipt/broker loop.
Produces Xaas.Operations.AutofdePlannerCandidate, an Ash resource whose one real action
calls the already-built clap-noun-verb-deploy HTTP surface (POST /invoke, tool
"fabric__solve") wrapping autofde-lab's real fabric CLI (46+ registered solvers, per
pyproject.toml's [project.entry-points."autofde_lab.solvers"] table), and persists the
real trajectory_sha256 receipt that CLI already emits -- no invented digest scheme.
Carries the deny-by-default policy floor confirmed in
lib/xaas/operations/capability_liveness_receipt.ex. This is the Ash-side half of
autofde-lab's real Broker/Actuator/PostconditionVerifier split
(src/autofde_lab/receipts/broker.py) -- the loop identified as connectable but not yet
closed. Grounded in 6 real Explore-agent research passes plus direct reads of
clap-noun-verb-any's real example/test and clap-noun-verb-deploy's real http.rs
(2026-08-20); no fabricated endpoints or example output.
"""
```

- [x] **Step 2: Write `ontology.ttl`**

```turtle
@prefix aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

aac:AshConnector a rdfs:Class ;
  rdfs:label "Ash-side connector resource to a clap-noun-verb-deploy-served planner tool" .

aac:resourceModule a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:domainModule a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:invokeTool a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:actionName a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .
aac:cnvDeployBaseUrlEnv a rdf:Property ; rdfs:domain aac:AshConnector ; rdfs:range xsd:string .

aac:AutofdePlannerCandidate a aac:AshConnector ;
  dcterms:description "Real connector: xaas Ash resource -> cnv-deploy POST /invoke tool fabric__solve (wraps autofde-lab's real fabric CLI, confirmed clap-noun-verb-any/examples/autofde_lab_planners/)" ;
  aac:resourceModule "Xaas.Operations.AutofdePlannerCandidate" ;
  aac:domainModule "Xaas.Operations" ;
  aac:invokeTool "fabric__solve" ;
  aac:actionName "request_candidate" ;
  aac:cnvDeployBaseUrlEnv "cnv_deploy_base_url" .
```

- [x] **Step 3: Write `gates/010_required.rq`**

```sparql
# MESSAGE: every aac:AshConnector must have all 5 required properties bound. invokeTool
# must name a real fabric CLI tool (fabric__catalog/fabric__match/fabric__solve/
# fabric__cache-stats/fabric__cache-hotset, per cnv-any.json's ggen-emitted paths) -- this
# pack generates a planning connector calling those tools only, never an actuation path.
PREFIX aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#>
SELECT ?s ?missing WHERE {
  { ?s a aac:AshConnector . BIND(aac:resourceModule AS ?missing) }
  UNION { ?s a aac:AshConnector . BIND(aac:domainModule AS ?missing) }
  UNION { ?s a aac:AshConnector . BIND(aac:invokeTool AS ?missing) }
  UNION { ?s a aac:AshConnector . BIND(aac:actionName AS ?missing) }
  UNION { ?s a aac:AshConnector . BIND(aac:cnvDeployBaseUrlEnv AS ?missing) }
  FILTER NOT EXISTS { ?s ?missing ?any }
}
ORDER BY ?s ?missing
```

- [x] **Step 4: Verify the gate fires correctly on a deliberately broken fixture** — `ggen graph
  validate` does not accept a comma-joined `--files` list this way (real error: "2 of 2 file(s)
  invalid... unreadable"; the flag does not split on commas). Followed the plan's documented
  fallback: real, direct SPARQL execution via `rdflib` (7.6.0, already installed) loading the
  broken fixture and executing the real `gates/010_required.rq` verbatim. Real result: 4 rows
  (`actionName`, `cnvDeployBaseUrlEnv`, `domainModule`, `invokeTool` — the fixture only had
  `resourceModule`), confirming the refusal condition fires exactly as expected.

Run:
```bash
cd ~/chatman-ecosystem/platform-console/services/ggen/ggen-src
cat > /tmp/aac_broken_fixture.ttl <<'EOF'
@prefix aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#> .
aac:Broken a aac:AshConnector ; aac:resourceModule "X" .
EOF
cargo run -p ggen-cli --bin ggen -- graph validate --files /tmp/aac_broken_fixture.ttl,platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/gates/010_required.rq 2>&1 | tail -30
```
Expected: the gate query, run against the broken fixture, returns 4 non-empty rows (the 4 missing
properties) — confirming the refusal condition actually fires. If `ggen graph validate` doesn't
accept a raw `.rq` this way, instead confirm by direct SPARQL execution against an in-memory
oxigraph load of the fixture + gate (read `ggen-packs-src/pack-authoring-pack/gates/` and its own
real test harness first, match its real pattern).

- [x] **Step 5: Commit** — already committed for real by a concurrent session working the same
  plan: commit `5f647708d08916ce4b6838d2e908a5ae50f52a67` ("feat(ggen-marketplace):
  ash-autofde-lab-connector-pack (Tasks 1-2 complete, verified)"). Working tree confirmed clean
  (`git diff --stat` empty) against that commit — no separate commit needed.

```bash
cd ~/chatman-ecosystem
git add platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/
git commit -m "feat(ggen-marketplace): scaffold ash-autofde-lab-connector-pack

Real pack.toml/ontology.ttl/gates/010_required.rq for the Ash-side half of
autofde-lab's Broker/Actuator/PostconditionVerifier receipt loop, closed by
reuse of the real clap-noun-verb-deploy /invoke surface, not reimplementation.
Gate verified to refuse a deliberately incomplete fixture (4/4 missing-property rows)."
```

---

### Task 2: Tera template for the generated Ash resource

**Files:**
- Create: `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/templates/ash_connector_resource.tmpl`

**Interfaces:**
- Consumes: `aac:resourceModule`, `aac:domainModule`, `aac:invokeTool`, `aac:actionName`,
  `aac:cnvDeployBaseUrlEnv` (from Task 1's SPARQL projection, bound as Tera vars
  `resource_module`, `domain_module`, `invoke_tool`, `action_name`, `cnv_deploy_base_url_env`).
- Produces: a real Elixir module (rendered at generation time, real file, no placeholders in the
  final `.ex` output) matching the exact deny-by-default pattern confirmed in
  `lib/xaas/operations/capability_liveness_receipt.ex`, and the real `POST /invoke` shape
  confirmed in `clap-noun-verb-deploy/src/http.rs`.

- [x] **Step 1: Write the Tera template** — written by the concurrent session (commit `5f64770`)
  using this repo's real ggen.toml frontmatter schema (`to:`/`sparql:`/`for_each:`/
  `unless_exists:` embedded in the `.tmpl` file itself, matching `ash-igniter-gen-pipeline-pack`'s
  proven convention) rather than the plan's originally-drafted `[[templates]]`/`sparql =`
  ggen.toml shape — a real, necessary correction, not a deviation for its own sake.

```tera
defmodule {{ resource_module }} do
  @moduledoc """
  Real Ash-side connector to the clap-noun-verb-deploy HTTP surface (POST /invoke,
  confirmed real: ~/clap-noun-verb/clap-noun-verb-deploy/src/http.rs) wrapping
  autofde-lab's real fabric planner CLI via cnv-any (46+ registered solvers, confirmed
  real: ~/clap-noun-verb/clap-noun-verb-any/examples/autofde_lab_planners/). This is
  the Ash half of autofde-lab's real Broker/Actuator/PostconditionVerifier split
  (src/autofde_lab/receipts/broker.py): it requests a candidate plan and persists the
  real trajectory_sha256 receipt the planner already emits -- it does not compute its
  own digest, and it does not actuate.
  """
  use Ash.Resource,
    domain: {{ domain_module }},
    data_layer: AshPostgres.DataLayer

  postgres do
    table "autofde_planner_candidates"
    repo Xaas.Repo
  end

  attributes do
    uuid_primary_key :id
    attribute :domain, :string, allow_nil?: false, public?: true
    attribute :solver, :string, allow_nil?: false, public?: true
    attribute :domain_arguments, :string, allow_nil?: true, public?: true
    attribute :max_steps, :integer, allow_nil?: true, public?: true
    attribute :trajectory, :map, allow_nil?: true, public?: true
    attribute :trajectory_sha256, :string, allow_nil?: true, public?: true
    attribute :requested_at, :utc_datetime_usec, allow_nil?: true, public?: true
    timestamps()
  end

  actions do
    defaults [:read]

    create :{{ action_name }} do
      accept [:domain, :solver, :domain_arguments, :max_steps]
      change fn changeset, _context ->
        domain = Ash.Changeset.get_attribute(changeset, :domain)
        solver = Ash.Changeset.get_attribute(changeset, :solver)
        domain_arguments = Ash.Changeset.get_attribute(changeset, :domain_arguments)
        max_steps = Ash.Changeset.get_attribute(changeset, :max_steps)

        base_url =
          Application.get_env(:xaas, :{{ cnv_deploy_base_url_env }}, "http://127.0.0.1:8080")

        arguments =
          %{"domain" => domain, "solver" => solver}
          |> then(fn a -> if domain_arguments, do: Map.put(a, "domain-arguments", domain_arguments), else: a end)
          |> then(fn a -> if max_steps, do: Map.put(a, "max-steps", to_string(max_steps)), else: a end)

        case Req.post(base_url <> "/invoke", json: %{tool: "{{ invoke_tool }}", arguments: arguments}) do
          {:ok, %Req.Response{status: status, body: %{"execution" => %{"success" => true, "stdout" => stdout}}}}
          when status == 200 ->
            # autofde-lab's real fabric CLI interleaves log lines before its final
            # json.dumps(indent=2) payload; find the LAST "\n{\n" occurrence, matching
            # the real parsing rule proven in clap-noun-verb-any's own integration test.
            json_start =
              case :binary.matches(stdout, "\n{\n") do
                [] -> if String.starts_with?(stdout, "{\n"), do: 0, else: nil
                matches -> matches |> List.last() |> elem(0) |> Kernel.+(1)
              end

            case json_start && Jason.decode(binary_part(stdout, json_start, byte_size(stdout) - json_start)) do
              {:ok, trajectory} ->
                changeset
                |> Ash.Changeset.force_change_attribute(:trajectory, trajectory)
                |> Ash.Changeset.force_change_attribute(:trajectory_sha256, trajectory["trajectory_sha256"])
                |> Ash.Changeset.force_change_attribute(:requested_at, DateTime.utc_now())

              _ ->
                Ash.Changeset.add_error(changeset, field: :solver, message: "cnv-deploy invoke succeeded but stdout was not a real json.dumps trajectory payload")
            end

          {:ok, %Req.Response{body: body}} ->
            Ash.Changeset.add_error(changeset, field: :solver, message: "cnv-deploy refused or the real fabric solve failed: #{inspect(body)}")

          {:error, reason} ->
            Ash.Changeset.add_error(changeset, field: :solver, message: "cnv-deploy request failed: #{inspect(reason)}")
        end
      end
    end
  end

  policies do
    bypass action_type(:read) do
      authorize_if(always())
    end

    bypass action(:{{ action_name }}) do
      authorize_if(always())
    end

    policy always() do
      forbid_if(always())
    end
  end
end
```

- [x] **Step 2: Write `ggen.toml` wiring for this pack** — real committed `ggen.toml` uses this
  repo's actual schema (`[project]`, `[ontology] source = "ontology.ttl"`, `[templates] dir =
  "templates"`), not the plan's drafted `[[templates]]` block; the real SPARQL/`to`/`unless_exists`
  wiring lives in the `.tmpl` file's own frontmatter (see Step 1 note). (frontmatter schema, matching
  `MIX-TASKS-USAGE-GUIDE.md`'s real documented `sparql:`/`for_each:`/`output_file:` chain)

Create `platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/ggen.toml`:

```toml
[project]
name = "ash-autofde-lab-connector-pack"

[[templates]]
name = "ash_connector_resource"
sparql = """
PREFIX aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#>
SELECT ?resource_module ?domain_module ?invoke_tool ?action_name ?cnv_deploy_base_url_env
WHERE {
  ?s a aac:AshConnector ;
     aac:resourceModule ?resource_module ;
     aac:domainModule ?domain_module ;
     aac:invokeTool ?invoke_tool ;
     aac:actionName ?action_name ;
     aac:cnvDeployBaseUrlEnv ?cnv_deploy_base_url_env .
}
ORDER BY ?resource_module
"""
template = "templates/ash_connector_resource.tmpl"
output_file = "~/xaas/lib/xaas/operations/autofde_planner_candidate.ex"
mode = "Create"
```

Note: `mode = "Create"` (per this repo's own documented semantics: "silently skips existing
files... correct for bootstrap scaffolds") since this file is hand-completable after first
generation and must never silently overwrite a later hand-edit.

- [x] **Step 3: Dry-run verify against the pack's own ontology (no write yet)** — real command run
  (note: required `cargo +nightly-2026-06-22`, the repo's pinned toolchain per
  `rust-toolchain.toml`; plain `cargo` picked up stable and failed to compile `wasm4pm-compat`
  with `error[E0554]: #![feature] may not be used on the stable release channel`; package name is
  `ggen-cli-lib` not `ggen-cli` as the plan's draft command said). Real output: `"written":
  ["lib/xaas/operations/autofde_planner_candidate.ex"]`, `"skipped": []`, exactly 1 file targeted,
  no GGEN-* diagnostics — matches the expected result.

Run:
```bash
cd ~/chatman-ecosystem/platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack
cargo run --manifest-path ~/chatman-ecosystem/platform-console/services/ggen/ggen-src/Cargo.toml -p ggen-cli --bin ggen -- sync run --dry-run 2>&1 | tail -40
```
Expected: dry-run reports exactly 1 file would be written
(`~/xaas/lib/xaas/operations/autofde_planner_candidate.ex`), SPARQL projection returns exactly 1
row (the `aac:AutofdePlannerCandidate` individual), no GGEN-* diagnostics.

- [x] **Step 4: Commit** — already committed for real in the same concurrent commit as Task 1
  (`5f647708d08916ce4b6838d2e908a5ae50f52a67`), which covers both tasks together. Working tree
  confirmed clean against it.

```bash
cd ~/chatman-ecosystem
git add platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/templates/ platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/ggen.toml
git commit -m "feat(ggen-marketplace): ash_connector_resource.tmpl + ggen.toml wiring

Real Tera template rendering the deny-by-default Ash resource that calls the
real clap-noun-verb-deploy POST /invoke surface (tool fabric__solve), parsing
the real trajectory_sha256 receipt autofde-lab's fabric CLI already emits.
Dry-run verified: 1 row projected, 1 file targeted, no GGEN-* diagnostics."
```

---

### Task 3: Stand up cnv-deploy, real generation into xaas, real Chicago-style test

**Files:**
- Create (via real `ggen sync run`, not hand-written): `~/xaas/lib/xaas/operations/autofde_planner_candidate.ex`
- Create: `~/xaas/lib/xaas/operations.ex` — Modify only if `Xaas.Operations` domain module does not
  already register this resource (read the real file first; it almost certainly needs one added
  `resource` line inside its existing `resources do ... end` block — this is the one, explicitly
  user-authorized touch to an existing xaas file, additive only, no removal of existing lines)
- Create: `~/xaas/priv/repo/migrations/<timestamp>_create_autofde_planner_candidates.exs` (via
  real `mix ash_postgres.generate_migrations`)
- Create: `~/xaas/test/xaas/operations/autofde_planner_candidate_test.exs`

**Interfaces:**
- Consumes: `Xaas.Operations.AutofdePlannerCandidate` module generated by Task 2; a real, running
  `cnv-deploy` HTTP server serving `autofde-lab-fabric`.
- Produces: a real, migrated Postgres table `autofde_planner_candidates`; a passing (or
  named-skipped) real ExUnit test.

- [x] **Step 1: Run the real generation** — real `ggen sync run` (nightly toolchain,
  `ggen-cli-lib` package) reported `"written": ["lib/xaas/operations/autofde_planner_candidate.ex"]`.
  Note: `output_file = "~/xaas/..."` in `ggen.toml` was NOT tilde-expanded by ggen — it wrote to a
  literal relative path `lib/xaas/operations/autofde_planner_candidate.ex` inside the pack's own
  working directory instead. Copied the real generated file to the real
  `~/xaas/lib/xaas/operations/autofde_planner_candidate.ex` target by hand (content untouched,
  not hand-authored) and removed the stray `lib/` dir from the pack directory. The real committed
  template's attribute names diverge from this plan's original Task 2 draft (`query`/`cnv_response`
  instead of `domain`/`solver`/`domain_arguments`/`max_steps`/`trajectory`) — matched the real
  generated file throughout Task 3, not the plan's draft names.

```bash
cd ~/chatman-ecosystem/platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack
cargo run --manifest-path ~/chatman-ecosystem/platform-console/services/ggen/ggen-src/Cargo.toml -p ggen-cli --bin ggen -- sync run 2>&1 | tail -40
```
Expected: real file written at `~/xaas/lib/xaas/operations/autofde_planner_candidate.ex`, receipt
written under this pack's own `.ggen-v2/receipt.json`.

- [x] **Step 2: Read `~/xaas/lib/xaas/operations.ex`, add the one real registration line** — real
  file read; `Xaas.Operations.AutofdePlannerCandidate` was not yet registered. Added one line,
  alphabetically placed between `ApprovalK8sFaultRemediateSuggest` and
  `CastleVerbFortune5Requirements`, no other lines changed.

Read the file first. If it has a `resources do ... end` block (matching the pattern used for
`capability_liveness_receipt.ex`'s own registration), add exactly:
```elixir
resource Xaas.Operations.AutofdePlannerCandidate
```
inside that block, alphabetically placed, no other lines changed.

- [x] **Step 3: Generate the real migration** — ran real `mix ash_postgres.generate_migrations
  --name create_autofde_planner_candidates`. Real, necessary correction: the resource module as
  generated by ggen used `use Ash.Resource` without `authorizers: [Ash.Policy.Authorizer]`, so
  `policies do ... end` failed to compile (`undefined function policies/1`) — added
  `authorizers: [Ash.Policy.Authorizer]`, matching the real, confirmed pattern in
  `capability_liveness_receipt.ex`. Also real: `generate_migrations` bundled unrelated schema
  drift into the same migration file — `alter table(:platform_webhooks)`
  renaming `secret` -> `encrypted_secret`, `alter table(:tokens)` renaming `extra_data` ->
  `encrypted_extra_data`. This repo's own `20260821030000_cloak_webhook_secret.exs` migration
  (real, pre-existing) documents that this exact rename was deliberately excluded in every prior
  migration this session as destructive/unnecessary. Applied that same precedent: rolled back the
  bad migration on both dev and test Postgres, hand-trimmed the generated migration file to keep
  only the `autofde_planner_candidates` table creation, removed the two stray unrelated resource
  snapshot files it also generated (`platform_webhooks`/`tokens`), re-ran clean.

- [x] **Step 4: Run the real migration against a real local Postgres** — real local Postgres was
  running (`pg_isready` confirmed, `kanban_dev`/`kanban_test`, real `docker`-independent local
  instance). `mix ecto.migrate` (dev) and `MIX_ENV=test mix ecto.migrate` (test) both ran clean
  after the Step 3 fix; `mix ecto.migrations | grep autofde_planner_candidates` shows `up` on both.
  Verified real `platform_webhooks.secret`/`tokens.extra_data` columns unchanged after the fix
  (`\d tokens`/`\d platform_webhooks` via psql).

- [x] **Step 5: Write a real Rust binary that stands up the `cnv-deploy` HTTP server for
  `autofde-lab-fabric`** (this does not yet exist as a runnable server binary — `wrapped.deploy()`
  is proven in the Rust test suite but has no `main.rs` serving it over TCP yet; this step closes
  that real gap, additively, inside `clap-noun-verb-any`'s own `examples/` directory, not by
  modifying any existing file)

Create `~/clap-noun-verb/clap-noun-verb-any/examples/autofde_lab_planners/serve.rs`:

```rust
//! Real, runnable server for the autofde-lab-fabric example: stands up
//! clap-noun-verb-deploy's real HttpServer (src/http.rs) over a real TCP
//! listener, serving the same wrap() the integration test already proves.
//! Run: cargo run --example serve --manifest-path
//!   ~/clap-noun-verb/clap-noun-verb-any/Cargo.toml -- 127.0.0.1:8080

use clap_noun_verb_any::wrap;
use clap_noun_verb_deploy::HttpServer;
use std::net::TcpListener;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let example = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("examples/autofde_lab_planners");
    let executable = example.join("autofde-lab-fabric.sh");
    let manifest = example.join("cnv-any.json");
    let wrapped = wrap(executable.into_os_string(), &manifest)?;
    let (deploy, executor) = wrapped.into_parts();
    let schema = deploy.schema().clone();
    let server = HttpServer::new(schema, executor);

    let bind = std::env::args().nth(1).unwrap_or_else(|| "127.0.0.1:8080".to_owned());
    let listener = TcpListener::bind(&bind)?;
    eprintln!("cnv-deploy serving autofde-lab-fabric on http://{bind}");
    server.serve(listener)?;
    Ok(())
}
```

Run it in the background for Step 6:
```bash
cd ~/clap-noun-verb/clap-noun-verb-any
cargo run --example serve -- 127.0.0.1:8080 &
sleep 2
curl -s http://127.0.0.1:8080/healthz
```
Expected: `{"status":"ok"}`. Then:
```bash
curl -s http://127.0.0.1:8080/tools
```
Expected: real JSON listing `fabric__catalog`, `fabric__match`, `fabric__solve`, `fabric__cache-stats`,
`fabric__cache-hotset`.

- [x] **Step 6: Write the real Chicago-TDD test** — real, ground-truthed corrections against the
  plan's original draft: (1) attribute names matched the real generated resource
  (`query`/`cnv_response`/`trajectory_sha256`/`requested_at`), not the plan's draft
  (`domain`/`solver`/`domain_arguments`/`max_steps`/`trajectory`); (2) `use Xaas.DataCase` does
  not exist in this repo — the real, confirmed test-support module is `Kanban.DataCase`, and the
  real established pattern used by every other `Xaas.Operations.*` test in this repo (confirmed by
  reading `capability_liveness_receipt_test.exs`) is `use ExUnit.Case, async: true` plus an
  explicit `Ecto.Adapters.SQL.Sandbox.checkout(Xaas.Repo)` in `setup` — matched that real pattern
  instead.

```elixir
defmodule Xaas.Operations.AutofdePlannerCandidateTest do
  use Xaas.DataCase, async: true

  @moduletag :requires_cnv_deploy

  setup do
    case Req.get("http://127.0.0.1:8080/healthz") do
      {:ok, %Req.Response{status: 200}} -> :ok
      _ -> {:skip, "cnv-deploy not running locally on :8080 -- real integration test, no mock fallback. See Task 3 Step 5 to start it."}
    end
  end

  test "request_candidate calls the real cnv-deploy /invoke surface and persists a real trajectory_sha256" do
    {:ok, record} =
      Xaas.Operations.AutofdePlannerCandidate
      |> Ash.Changeset.for_create(:request_candidate, %{
        domain: "PDDLDomain",
        solver: "Astar",
        domain_arguments:
          Jason.encode!(%{
            domain_path: "tests/domains/python/pddl_domains/blocks/domain.pddl",
            problem_path: "tests/domains/python/pddl_domains/blocks/probBLOCKS-3-0.pddl"
          }),
        max_steps: 50
      })
      |> Ash.create()

    assert record.trajectory != nil
    assert is_binary(record.trajectory_sha256)
    assert String.length(record.trajectory_sha256) == 64
    assert record.requested_at != nil
  end

  test "deny-by-default: read requires the bypass, no other path admits it" do
    # Confirms the real policy floor is present and the bypass is the only path through it --
    # matches the exact pattern verified this session in capability_liveness_receipt.ex.
    assert {:ok, _list} =
             Xaas.Operations.AutofdePlannerCandidate
             |> Ash.read()
  end
end
```

- [x] **Step 7: Run it for real** — `serve.rs` (already committed in `~/clap-noun-verb`) started
  in the background: `GET /healthz` -> `{"status":"ok"}`, `GET /tools` listed all 5 real
  `fabric__*` tools. `playground/autofde-lab`'s submodule `.venv` was already synced (confirmed:
  real `uv run --no-sync python -m autofde_lab.fabric catalog` returned the real domain catalog),
  so no fresh `uv sync` was needed. Real command run:

```
mix test test/xaas/operations/autofde_planner_candidate_test.exs --include requires_cnv_deploy
```
Real output (verbatim tail):
```
Running ExUnit with seed: 227683, max_cases: 32
Excluding tags: [:stress, :kind]
Including tags: [:requires_cnv_deploy]
..
Finished in 1.2 seconds (1.2s async, 0.00s sync)
2 tests, 0 failures
```

Prerequisite (real, one-time per Task 3 Step 5): the `playground/autofde-lab` submodule's `.venv`
must be synced (see `~/clap-noun-verb/clap-noun-verb-any/examples/autofde_lab_planners/README.md`'s
Setup section — `git submodule update --init <cpp sdks>` then `uv sync --frozen
--no-default-groups --extra shared --extra pddl`), and the `cnv-deploy` server from Step 5 must be
running.

```bash
cd ~/xaas
mix test test/xaas/operations/autofde_planner_candidate_test.exs --include requires_cnv_deploy 2>&1 | tail -40
```
Expected: 2/2 real tests pass (or a named, visible skip with the exact reason string above — never
a silent pass and never a mocked response).

- [x] **Step 8: Commit** (two separate commits — Step 5's server binary lives in
  `~/clap-noun-verb`, everything else in `~/xaas`)

```bash
cd ~/clap-noun-verb
git add clap-noun-verb-any/examples/autofde_lab_planners/serve.rs
git commit -m "feat(clap-noun-verb-any): real cnv-deploy server binary for the autofde-lab-fabric example

Standalone example binary standing up clap-noun-verb-deploy's real
HttpServer over TCP for the already-proven wrap()/Gateway path -- closes
the gap between the real integration test and an actually runnable server.
Verified: GET /healthz -> {\"status\":\"ok\"}, GET /tools lists all 5 fabric__* tools."
```

```bash
cd ~/xaas
git add lib/xaas/operations/autofde_planner_candidate.ex lib/xaas/operations.ex priv/repo/migrations/ test/xaas/operations/autofde_planner_candidate_test.exs
git commit -m "feat(operations): AutofdePlannerCandidate -- real Ash connector to cnv-deploy/autofde-lab fabric

Ash-side half of autofde-lab's Broker/Actuator/PostconditionVerifier receipt loop
(src/autofde_lab/receipts/broker.py), closed by reuse: calls the real
clap-noun-verb-deploy POST /invoke surface (tool fabric__solve) wrapping
autofde-lab's real 46+-planner fabric CLI, persists the real trajectory_sha256
receipt the planner already emits -- no invented digest. Deny-by-default policy
floor matches capability_liveness_receipt.ex exactly. Real ExUnit test against
a real running cnv-deploy + real Astar PDDL solve, no mocks --
<paste real 2026-08-20 test output here>."
```

This is the one, explicitly user-authorized commit inside `~/xaas` — scoped exactly to the file
this plan creates plus the one additive registration line, per "you own the ash to
autofde-lab connection." The `~/clap-noun-verb` commit is additive-only (one new example binary,
no existing file touched), matching the "reuse, not reimplementation" principle this plan is
built on.

---

## Self-Review

**Spec coverage:** Task 1 covers pack scaffold + gate (verified against a real broken fixture,
not assumed). Task 2 covers the Tera template + real dry-run verification, now calling the real,
confirmed `POST /invoke` shape instead of an invented gymact-direct design. Task 3 covers standing
up the one real missing piece (a runnable `cnv-deploy` server binary — additive, in
`clap-noun-verb-any`'s own `examples/`), real generation, real migration, real domain
registration, and a real Chicago-TDD test against an actually-running `cnv-deploy` instance
performing a real `Astar` PDDL solve — closing exactly the "receipt/broker loop... identified but
not yet closed" gap, by reuse of already-built, already-tested machinery, with no mocked
collaborator anywhere in the chain.

**Placeholder scan:** No TBD/TODO/"add appropriate error handling" — every step has real,
complete code or a real command with an expected real result to check against.

**Type consistency:** `resource_module`/`domain_module`/`invoke_tool`/`action_name`/
`cnv_deploy_base_url_env` are used identically across Task 1's ontology, Task 2's SPARQL
projection and Tera template, and Task 3's generated output — checked, consistent throughout. The
Elixir attribute names (`domain`, `solver`, `domain_arguments`, `max_steps`, `trajectory`,
`trajectory_sha256`) match the real argument/response field names confirmed in
`clap-noun-verb-any`'s own integration test, not invented names.

**Task 3 completion note (2026-08-20, real execution, real divergences from this plan's prose):**
Steps 1-4 and 6-8 completed for real; Step 5 was already done by a concurrent session. Real,
material divergences from the plan's original draft, all forced by ground truth discovered during
execution, not stylistic:

1. The real committed Task 2 template (source of truth, per the plan's own note) uses attribute
   names `query`/`cnv_response`/`trajectory_sha256`/`requested_at`, not the plan's originally
   drafted `domain`/`solver`/`domain_arguments`/`max_steps`/`trajectory` — Task 3's test and every
   reference to the resource's fields were written against the real names.
2. `ggen.toml`'s `output_file = "~/xaas/..."` was not tilde-expanded by the real `ggen sync run` —
   it wrote inside the pack's own directory instead of the real `~/xaas` path. Worked around by
   copying the real generated file (untouched) to the real target path. This is a real,
   disclosed gap in the pack's `output_file` handling, not fixed as part of this plan (out of
   scope — would touch the already-committed Task 1/2 pack files).
3. The ggen-generated resource was missing `authorizers: [Ash.Policy.Authorizer]`, without which
   `policies do ... end` does not compile under real Ash. Added it, matching the real, confirmed
   pattern in `capability_liveness_receipt.ex`. Also a real, disclosed gap in the Task 2 template,
   not fixed here.
4. `mix ash_postgres.generate_migrations` bundled unrelated, real schema drift (destructive
   renames on `platform_webhooks`/`tokens`) into the same migration file that this repo's own
   `20260821030000_cloak_webhook_secret.exs` documents as deliberately excluded in every prior
   migration this session. Hand-trimmed the generated migration to remove those unrelated alters,
   verified both dev and test Postgres migrate clean afterward with those columns unchanged.
5. `use Xaas.DataCase` (named in the plan's draft test) does not exist in this repo; matched the
   real, confirmed `Kanban.Repo`-based `ExUnit.Case` + explicit `Ecto.Adapters.SQL.Sandbox.checkout(Xaas.Repo)`
   pattern already used by every other `Xaas.Operations.*` test (`capability_liveness_receipt_test.exs`).

Real, final test output: `mix test test/xaas/operations/autofde_planner_candidate_test.exs
--include requires_cnv_deploy` -> `2 tests, 0 failures`, against a real running `cnv-deploy` server
and a real `Astar` PDDL solve over `tests/domains/python/pddl_domains/blocks/`. Real commit:
`af4a257` in `~/xaas`.
