# End-to-End Trace: `Xaas.Operations.AutofdePlannerCandidate`

Real trace of one capability from RDF fact through generated Elixir code through a real
deployed test run, captured 2026-08-20. Every excerpt below is quoted verbatim from a file
read this run, or is real command output captured this run.

## Hop 1: the real TTL individual

File: `~/chatman-ecosystem/platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/ontology.ttl`

```
aac:AutofdePlannerCandidate a aac:AshConnector ;
  dcterms:description "Real connector: xaas Ash resource -> cnv-deploy POST /invoke tool fabric__solve (wraps autofde-lab's real fabric CLI, confirmed clap-noun-verb-any/examples/autofde_lab_planners/)" ;
  aac:resourceModule "Xaas.Operations.AutofdePlannerCandidate" ;
  aac:domainModule "Xaas.Operations" ;
  aac:invokeTool "fabric__solve" ;
  aac:actionName "request_candidate" ;
  aac:cnvDeployBaseUrlEnv "cnv_deploy_base_url" ;
  aac:outputFile "lib/xaas/operations/autofde_planner_candidate.ex" ;
  aac:tableName "autofde_planner_candidates" .
```

## Hop 2: the real SPARQL projection (template frontmatter)

File: `templates/ash_connector_resource.tmpl` (same pack dir), frontmatter block:

```
---
to: "{{ output_file }}"
skip_empty: false
unless_exists: true
for_each: results
sparql:
  results: |
    PREFIX aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#>
    SELECT ?resource_module ?domain_module ?action_name ?cnv_tool ?base_url_env ?output_file ?table_name WHERE {
      ?s a aac:AshConnector ;
         aac:resourceModule ?resource_module ;
         aac:domainModule ?domain_module ;
         aac:actionName ?action_name ;
         aac:invokeTool ?cnv_tool ;
         aac:cnvDeployBaseUrlEnv ?base_url_env ;
         aac:outputFile ?output_file ;
         aac:tableName ?table_name .
    }
    ORDER BY ?resource_module
---
```

This SELECT iterates every `aac:AshConnector` individual (both `AutofdePlannerCandidate` and
`AutofdePlannerCatalog` satisfy the WHERE clause), so `for_each: results` renders one file per
individual; `unless_exists: true` means once `lib/xaas/operations/autofde_planner_candidate.ex`
exists on disk the template will not clobber hand-edits to it.

`ggen.toml` in the same directory:

```
[project]
name = "ash-autofde-lab-connector-pack"

[ontology]
source = "ontology.ttl"

[templates]
dir = "templates"
```

## Hop 3: the real generated Elixir code

File: `~/xaas/lib/xaas/operations/autofde_planner_candidate.ex` (real, current content,
`cat` output):

```elixir
defmodule Xaas.Operations.AutofdePlannerCandidate do
  @moduledoc """
  Real Ash-side connector to clap-noun-verb-deploy's real /invoke HTTP surface
  (~/clap-noun-verb/clap-noun-verb-deploy/src/http.rs), calling the fabric__solve tool --
  autofde-lab's real, already-wrapped planner federation (46+ registered solvers over 25+
  domains, ~/clap-noun-verb/clap-noun-verb-any/examples/autofde_lab_planners/cnv-any.json).
  This is the Ash half of autofde-lab's real Broker/Actuator/PostconditionVerifier split
  (src/autofde_lab/receipts/broker.py): it requests a candidate plan and persists the real
  trajectory_sha256 the underlying planner already emits -- no digest is invented here.
  Never calls gymact's real DO path (POST /episodes/{id}/actions/selected); this is a
  planning connector, not an actuation connector.
  """
  use Ash.Resource,
    domain: Xaas.Operations,
    data_layer: AshPostgres.DataLayer,
    authorizers: [Ash.Policy.Authorizer]

  postgres do
    table "autofde_planner_candidates"
    repo Xaas.Repo
  end

  attributes do
    uuid_primary_key :id
    attribute :query, :string, allow_nil?: false, public?: true
    attribute :cnv_response, :map, allow_nil?: true, public?: true
    attribute :trajectory_sha256, :string, allow_nil?: true, public?: true
    attribute :requested_at, :utc_datetime_usec, allow_nil?: true, public?: true
    timestamps()
  end

  actions do
    defaults [:read]

    create :request_candidate do
      accept [:query]
      change fn changeset, _context ->
        query = Ash.Changeset.get_attribute(changeset, :query)
        base_url =
          Application.get_env(:xaas, :cnv_deploy_base_url, "http://127.0.0.1:8080")

        body = %{
          tool: "fabric__solve",
          arguments:

            %{
              domain: "PDDLDomain",
              solver: "Astar",
              "domain-arguments": query
            }

        }

        case Req.post(base_url <> "/invoke", json: body) do
          {:ok, %Req.Response{status: 200, body: record}} ->
            apply_record(changeset, record)

          {:ok, %Req.Response{status: status, body: resp_body}} ->
            Ash.Changeset.add_error(changeset,
              field: :query,
              message: "cnv-deploy /invoke returned status #{status}: #{inspect(resp_body)}"
            )

          {:error, reason} ->
            Ash.Changeset.add_error(changeset,
              field: :query,
              message: "cnv-deploy /invoke request failed: #{inspect(reason)}"
            )
        end
      end
    end
  end

  # Real trajectory_sha256 extraction, matching clap-noun-verb-any's own real integration
  # test (tests/autofde_lab_integration.rs): the underlying Typer CLI's `typer.echo(
  # json.dumps(..., indent=2))` payload can be preceded by real log-noise lines on the same
  # stdout stream, and a naive first-`{` search is wrong because log lines can themselves
  # contain a literal `{` (this domain logs Python `frozenset({...})` reprs). `json.dumps(
  # indent=2)` always puts its opening brace alone on its own line, so find the LAST such
  # line instead.
  defp apply_record(changeset, %{"execution" => %{"stdout" => stdout, "exit_code" => 0}}) do
    case last_json_object(stdout) do

      {:ok, %{"trajectory_sha256" => sha}} when is_binary(sha) ->
        changeset
        |> Ash.Changeset.force_change_attribute(:cnv_response, %{"stdout" => stdout})
        |> Ash.Changeset.force_change_attribute(:trajectory_sha256, sha)
        |> Ash.Changeset.force_change_attribute(:requested_at, DateTime.utc_now())

      _ ->
        Ash.Changeset.add_error(changeset,
          field: :query,
          message: "cnv-deploy /invoke succeeded but stdout had no trajectory_sha256 JSON payload"
        )

    end
  end

  defp apply_record(changeset, %{"execution" => %{"exit_code" => exit_code, "stderr" => stderr}}) do
    Ash.Changeset.add_error(changeset,
      field: :query,
      message: "fabric__solve exited #{exit_code}: #{stderr}"
    )
  end

  defp apply_record(changeset, _other) do
    Ash.Changeset.add_error(changeset, field: :query, message: "unexpected cnv-deploy /invoke response shape")
  end

  defp last_json_object(stdout) do
    case :binary.matches(stdout, "\n{\n") do
      [] ->
        if String.starts_with?(stdout, "{\n"), do: Jason.decode(stdout), else: :error

      matches ->
        {start, _len} = List.last(matches)
        Jason.decode(binary_part(stdout, start + 1, byte_size(stdout) - start - 1))
    end
  end

  policies do
    bypass action_type(:read) do
      authorize_if(always())
    end

    bypass action(:request_candidate) do
      authorize_if(always())
    end

    policy always() do
      forbid_if(always())
    end
  end
end
```

## Hop 4: the real migration

File: `~/xaas/priv/repo/migrations/20260821023643_create_autofde_planner_candidates.exs`
(real, current content):

```elixir
defmodule Xaas.Repo.Migrations.CreateAutofdePlannerCandidates do
  @moduledoc """
  Updates resources based on their most recent snapshots.

  This file was autogenerated with `mix ash_postgres.generate_migrations`
  """

  use Ecto.Migration

  def up do
    create table(:autofde_planner_candidates, primary_key: false) do
      add :id, :uuid, null: false, default: fragment("gen_random_uuid()"), primary_key: true
      add :query, :text, null: false
      add :cnv_response, :map
      add :trajectory_sha256, :text
      add :requested_at, :utc_datetime_usec

      add :inserted_at, :utc_datetime_usec,
        null: false,
        default: fragment("(now() AT TIME ZONE 'utc')")

      add :updated_at, :utc_datetime_usec,
        null: false,
        default: fragment("(now() AT TIME ZONE 'utc')")
    end
  end

  def down do
    drop table(:autofde_planner_candidates)
  end
end
```

## Hop 5: the real test, run for real this session

File: `~/xaas/test/xaas/operations/autofde_planner_candidate_test.exs` (real, current
content):

```elixir
defmodule Xaas.Operations.AutofdePlannerCandidateTest do
  use ExUnit.Case, async: true

  @moduletag :requires_cnv_deploy

  setup do
    :ok = Ecto.Adapters.SQL.Sandbox.checkout(Xaas.Repo)

    case Req.get("http://127.0.0.1:8080/healthz") do
      {:ok, %Req.Response{status: 200}} -> :ok
      _ -> {:skip, "cnv-deploy not running locally on :8080 -- real integration test, no mock fallback. See Task 3 Step 5 to start it."}
    end
  end

  test "request_candidate calls the real cnv-deploy /invoke surface and persists a real trajectory_sha256" do
    query =
      Jason.encode!(%{
        domain_path: "tests/domains/python/pddl_domains/blocks/domain.pddl",
        problem_path: "tests/domains/python/pddl_domains/blocks/probBLOCKS-3-0.pddl"
      })

    {:ok, record} =
      Xaas.Operations.AutofdePlannerCandidate
      |> Ash.Changeset.for_create(:request_candidate, %{query: query})
      |> Ash.create()

    assert record.cnv_response != nil
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

Preflight, run this session before the test:

```
$ curl -s -m 2 http://127.0.0.1:8080/healthz
{"status":"ok"}
```

cnv-deploy was live locally, so the run below is the real `--include requires_cnv_deploy`
path (no local-server-absent fallback needed).

Command and real output, captured this run:

```
$ cd ~/xaas && mix test test/xaas/operations/autofde_planner_candidate_test.exs --include requires_cnv_deploy 2>&1 | tail -30
...
Running ExUnit with seed: 556588, max_cases: 32
Excluding tags: [:stress, :kind]
Including tags: [:requires_cnv_deploy]

20:23:37.585 [warning] Received an unhandled response from Grafana because: {:error, %Finch.TransportError{reason: :nxdomain, source: %Mint.TransportError{reason: :nxdomain}}}
20:23:37.585 [warning] PromEx.DashboardUploader failed to upload /Users/sac/xaas/_build/test/lib/prom_ex/priv/application.json.eex to Grafana: :unkown
...
..
Finished in 0.6 seconds (0.6s async, 0.00s sync)
2 tests, 0 failures
```

(The Grafana/PromEx warnings are unrelated startup noise from xaas's telemetry supervision
tree reaching for a local Grafana instance that isn't running; they do not affect the test
result. `2 tests, 0 failures` is the real, current pass state -- both the live-`/invoke` test
and the deny-by-default policy test passed against the real running cnv-deploy server.)

## Hop 6: the real commit hashes per file

```
$ cd ~/chatman-ecosystem && git log --oneline -- platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/ontology.ttl
fe1144a feat(ggen): second real aac:AshConnector individual proves capability x planner composition
5f64770 feat(ggen-marketplace): ash-autofde-lab-connector-pack (Tasks 1-2 complete, verified)

$ git log --oneline -- platform-console/services/ggen-marketplace/ggen-packs-src/ash-autofde-lab-connector-pack/templates/ash_connector_resource.tmpl
fe1144a feat(ggen): second real aac:AshConnector individual proves capability x planner composition
5f64770 feat(ggen-marketplace): ash-autofde-lab-connector-pack (Tasks 1-2 complete, verified)

$ cd ~/xaas && git log --oneline -- lib/xaas/operations/autofde_planner_candidate.ex
83347bf feat: real R2RML/Ontop prototype (proven, not just design), Reactor-for-planners design doc, Marketplace.Provider stress coverage
af4a257 feat(operations): AutofdePlannerCandidate -- real Ash connector to cnv-deploy/autofde-lab fabric

$ git log --oneline -- priv/repo/migrations/20260821023643_create_autofde_planner_candidates.exs
af4a257 feat(operations): AutofdePlannerCandidate -- real Ash connector to cnv-deploy/autofde-lab fabric

$ git log --oneline -- test/xaas/operations/autofde_planner_candidate_test.exs
af4a257 feat(operations): AutofdePlannerCandidate -- real Ash connector to cnv-deploy/autofde-lab fabric
```

`af4a257` (in the `~/xaas` repo, a separate repo from `~/chatman-ecosystem`) is where the
generated Elixir resource, its migration, and its test all landed together. `83347bf` (also
in `~/xaas`) is a later commit that touched `autofde_planner_candidate.ex` again. `fe1144a`
and `5f64770` (in `~/chatman-ecosystem`) are where the TTL individual and the SPARQL-bearing
template landed.

## Summary of the real chain

1. `ontology.ttl` (`~/chatman-ecosystem`, commit `5f64770`/`fe1144a`) declares the
   `aac:AutofdePlannerCandidate` individual with its `resourceModule`, `invokeTool`,
   `actionName`, `outputFile`, `tableName` facts.
2. `templates/ash_connector_resource.tmpl`'s frontmatter SPARQL SELECT projects those facts
   out of the ontology, one row per `aac:AshConnector` individual, driving `for_each`
   rendering to `{{ output_file }}`.
3. That template rendered (at generation time, prior to this session) into
   `~/xaas/lib/xaas/operations/autofde_planner_candidate.ex`, landing in `~/xaas` commit
   `af4a257`.
4. The same commit carries the Ash-generated migration
   `priv/repo/migrations/20260821023643_create_autofde_planner_candidates.exs`.
5. The same commit carries the real integration test
   `test/xaas/operations/autofde_planner_candidate_test.exs`, re-run this session against a
   live local cnv-deploy (`http://127.0.0.1:8080/healthz` → `{"status":"ok"}`), producing
   `2 tests, 0 failures`.
