defmodule Xaas.Operations.AutofdePlannerCacheHotset do
  @moduledoc """
  Real Ash-side connector to clap-noun-verb-deploy's real /invoke HTTP surface
  (~/clap-noun-verb/clap-noun-verb-deploy/src/http.rs), calling the fabric__cache-hotset tool --
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
    table "autofde_planner_cache_hotset_requests"
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

    create :request_cache_hotset do
      accept [:query]
      change fn changeset, _context ->
        query = Ash.Changeset.get_attribute(changeset, :query)
        base_url =
          Application.get_env(:xaas, :cnv_deploy_base_url, "http://127.0.0.1:8080")

        body = %{
          tool: "fabric__cache-hotset",
          arguments:

            %{}

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

      {:ok, decoded} ->
        # fabric__cache-hotset does not emit a trajectory_sha256 (it is not a solve call), so
        # trajectory_sha256 stays nil here -- no digest is invented for a non-solve tool.
        changeset
        |> Ash.Changeset.force_change_attribute(:cnv_response, decoded)
        |> Ash.Changeset.force_change_attribute(:requested_at, DateTime.utc_now())

      :error ->
        Ash.Changeset.add_error(changeset,
          field: :query,
          message: "cnv-deploy /invoke succeeded but stdout had no parseable JSON payload"
        )

    end
  end

  defp apply_record(changeset, %{"execution" => %{"exit_code" => exit_code, "stderr" => stderr}}) do
    Ash.Changeset.add_error(changeset,
      field: :query,
      message: "fabric__cache-hotset exited #{exit_code}: #{stderr}"
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

    bypass action(:request_cache_hotset) do
      authorize_if(always())
    end

    policy always() do
      forbid_if(always())
    end
  end
end
