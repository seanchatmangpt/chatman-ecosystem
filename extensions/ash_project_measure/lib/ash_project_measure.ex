defmodule AshProjectMeasure do
  @moduledoc """
  Read-only Ash/Spark project measurement extension.

  It configures observation. It grants no mutation, release, deployment, or BRCE authority.
  """

  @github_actions %Spark.Dsl.Section{
    name: :github_actions,
    schema: [
      owner: [type: :string, required: true],
      activity_census_path: [type: :string, required: true],
      output_path: [type: :string, required: true],
      token_env: [type: :string, default: "GITHUB_TOKEN"],
      api_url: [type: :string, default: "https://api.github.com"]
    ]
  }

  @project_measure %Spark.Dsl.Section{
    name: :project_measure,
    sections: [@github_actions]
  }

  use Spark.Dsl.Extension, sections: [@project_measure]

  defmodule Info do
    @moduledoc false
    @path [:project_measure, :github_actions]

    def config(domain) do
      %{
        owner: opt(domain, :owner),
        activity_census_path: opt(domain, :activity_census_path),
        output_path: opt(domain, :output_path),
        token_env: opt(domain, :token_env, "GITHUB_TOKEN"),
        api_url: opt(domain, :api_url, "https://api.github.com")
      }
    end

    defp opt(domain, key, default \\ nil),
      do: Spark.Dsl.Extension.get_opt(domain, @path, key, default)
  end
end

defmodule AshProjectMeasure.Receipt do
  @moduledoc false
  @replay "recompute canonical JSON without receipt and require exact digest equality"

  def attach(observation) when is_map(observation) do
    observation = Map.delete(observation, "receipt")

    Map.put(observation, "receipt", %{
      "algorithm" => "sha256",
      "observation_digest" => digest(observation),
      "replay" => @replay
    })
  end

  def verify(%{"receipt" => %{"algorithm" => "sha256", "observation_digest" => expected}} = payload)
      when is_binary(expected) do
    digest(Map.delete(payload, "receipt")) == expected
  end

  def verify(_), do: false

  def digest(value) do
    value |> canonical_json() |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)
  end

  def canonical_json(value) when is_map(value) do
    body =
      value
      |> Enum.map(fn {key, item} -> {to_string(key), item} end)
      |> Enum.sort_by(&elem(&1, 0))
      |> Enum.map_join(",", fn {key, item} -> Jason.encode!(key) <> ":" <> canonical_json(item) end)

    "{" <> body <> "}"
  end

  def canonical_json(value) when is_list(value),
    do: "[" <> Enum.map_join(value, ",", &canonical_json/1) <> "]"

  def canonical_json(value)
      when is_binary(value) or is_number(value) or is_boolean(value) or is_nil(value),
      do: Jason.encode!(value)
end

defmodule AshProjectMeasure.GitHubActions do
  @moduledoc false
  @per_page 100
  @max_pages 100

  def list_workflow_runs(repository, since, until, opts \\ []) do
    with {:ok, owner, name} <- split_repository(repository) do
      fetch_pages(owner, name, since, until, opts, 1, nil, [])
    end
  end

  defp split_repository(repository) when is_binary(repository) do
    case String.split(repository, "/", parts: 2) do
      [owner, name] when owner != "" and name != "" -> {:ok, owner, name}
      _ -> {:error, "REFUSED[REPOSITORY_IDENTITY_INVALID] repo=#{repository}"}
    end
  end

  defp split_repository(repository),
    do: {:error, "REFUSED[REPOSITORY_IDENTITY_INVALID] repo=#{inspect(repository)}"}

  defp fetch_pages(owner, name, since, until, opts, page, expected_total, rows)
       when page <= @max_pages do
    query =
      URI.encode_query(%{
        "created" => "#{iso_z(since)}..#{iso_z(until)}",
        "page" => page,
        "per_page" => @per_page
      })

    path = "/repos/#{URI.encode(owner)}/#{URI.encode(name)}/actions/runs?#{query}"

    with {:ok, payload} <- request(path, opts),
         {:ok, page_rows, total} <- validate_payload(payload),
         :ok <- validate_total(expected_total, total, owner, name) do
      all_rows = rows ++ page_rows
      pages = max(1, div(total + @per_page - 1, @per_page))

      cond do
        page >= pages and length(all_rows) == total ->
          {:ok, all_rows}

        page >= pages ->
          {:error,
           "REFUSED[CI_RUN_SEARCH_TRUNCATED] repo=#{owner}/#{name} total_count=#{total} retrieved=#{length(all_rows)}"}

        true ->
          fetch_pages(owner, name, since, until, opts, page + 1, total, all_rows)
      end
    end
  end

  defp fetch_pages(owner, name, _since, _until, _opts, _page, _expected_total, _rows),
    do: {:error, "REFUSED[CI_RUN_PAGINATION_UNBOUNDED] repo=#{owner}/#{name}"}

  defp validate_payload(%{"workflow_runs" => rows, "total_count" => total})
       when is_list(rows) and is_integer(total) and total >= 0 do
    if Enum.all?(rows, &is_map/1),
      do: {:ok, rows, total},
      else: {:error, "REFUSED[CI_RUN_PAYLOAD_INVALID]"}
  end

  defp validate_payload(_), do: {:error, "REFUSED[CI_RUN_PAYLOAD_INVALID]"}
  defp validate_total(nil, _, _, _), do: :ok
  defp validate_total(total, total, _, _), do: :ok

  defp validate_total(expected, observed, owner, name),
    do:
      {:error,
       "REFUSED[CI_RUN_COUNT_DRIFT] repo=#{owner}/#{name} expected=#{expected} observed=#{observed}"}

  defp request(path, opts) do
    api_url = Keyword.get(opts, :api_url, "https://api.github.com") |> String.trim_trailing("/")
    token = Keyword.get(opts, :token)
    timeout = Keyword.get(opts, :timeout, 30_000)

    headers = [
      {~c"accept", ~c"application/vnd.github+json"},
      {~c"user-agent", ~c"ash-project-measure/1"},
      {~c"x-github-api-version", ~c"2022-11-28"}
    ]

    headers =
      if is_binary(token) and token != "",
        do: [{~c"authorization", String.to_charlist("Bearer " <> token)} | headers],
        else: headers

    case :httpc.request(
           :get,
           {String.to_charlist(api_url <> path), headers},
           [timeout: timeout],
           body_format: :binary
         ) do
      {:ok, {{_, status, _}, _, body}} when status in 200..299 ->
        case Jason.decode(body) do
          {:ok, payload} -> {:ok, payload}
          {:error, _} -> {:error, "REFUSED[CI_RUN_JSON_INVALID]"}
        end

      {:ok, {{_, status, _}, _, body}} ->
        {:error, "GitHub HTTP #{status}: #{String.slice(body, 0, 400)}"}

      {:error, reason} ->
        {:error, "GitHub transport failed: #{inspect(reason)}"}
    end
  end

  defp iso_z(%DateTime{} = value) do
    value |> DateTime.truncate(:second) |> DateTime.to_iso8601() |> String.replace("+00:00", "Z")
  end
end

defmodule AshProjectMeasure.Census do
  @moduledoc false
  alias AshProjectMeasure.{GitHubActions, Receipt}

  @schema "chatman.ash-project-measure.ci-outcome-census/1"
  @activity_prefix "chatman.portfolio-activity-census/"
  @failure_like ~w(action_required cancelled failure startup_failure timed_out)

  def observe!(domain, opts \\ []) do
    config = AshProjectMeasure.Info.config(domain)
    activity = config.activity_census_path |> File.read!() |> Jason.decode!()
    client_opts = [api_url: config.api_url, token: System.get_env(config.token_env)]

    case build(activity, config, Keyword.put_new(opts, :client_opts, client_opts)) do
      {:ok, payload} ->
        File.mkdir_p!(Path.dirname(config.output_path))
        File.write!(config.output_path, Jason.encode!(payload, pretty: true) <> "\n")
        summary = payload["summary"]

        IO.puts(
          "PARTIAL_ALIVE:ASH_PROJECT_MEASURE_CI_OUTCOME " <>
            "repositories=#{summary["admitted_repository_count"]} " <>
            "observed_ci=#{summary["repositories_with_observed_ci_runs"]} " <>
            "failure_like=#{summary["repositories_with_failure_like_outcomes"]} " <>
            "digest=#{payload["receipt"]["observation_digest"]}"
        )

        payload

      {:error, reason} ->
        raise reason
    end
  end

  def replay_file!(path) do
    payload = path |> File.read!() |> Jason.decode!()

    if Receipt.verify(payload) do
      IO.puts("ALIVE:ASH_PROJECT_MEASURE_CI_OUTCOME_REPLAY digest=#{payload["receipt"]["observation_digest"]}")
      :ok
    else
      raise "REFUSED[CI_OUTCOME_REPLAY_MISMATCH]"
    end
  end

  def build(activity, config, opts \\ [])

  def build(activity, config, opts) when is_map(activity) and is_map(config) do
    client = Keyword.get(opts, :client, &GitHubActions.list_workflow_runs/4)
    client_opts = Keyword.get(opts, :client_opts, [])

    with :ok <- validate_config(config),
         :ok <- ensure(Receipt.verify(activity), "ACTIVITY_CENSUS_RECEIPT"),
         :ok <- validate_schema(activity),
         {:ok, owner} <- validate_owner(activity, config),
         {:ok, since, until} <- parse_window(activity),
         {:ok, repositories} <- repositories(activity, owner),
         {:ok, ledgers} <- observe(client, client_opts, repositories, since, until) do
      {:ok, observation(activity, owner, since, until, ledgers) |> Receipt.attach()}
    end
  end

  def build(_, _, _), do: refusal("INPUT_INVALID")

  defp validate_config(config) do
    required = [:owner, :activity_census_path, :output_path, :token_env, :api_url]
    ensure(Enum.all?(required, &(is_binary(Map.get(config, &1)) and Map.get(config, &1) != "")), "ASH_EXTENSION_CONFIG_INCOMPLETE")
  end

  defp validate_schema(%{"schema" => schema}) when is_binary(schema),
    do: ensure(String.starts_with?(schema, @activity_prefix), "ACTIVITY_CENSUS_SCHEMA")

  defp validate_schema(_), do: refusal("ACTIVITY_CENSUS_SCHEMA")

  defp validate_owner(%{"owner" => owner}, %{owner: owner}) when is_binary(owner), do: {:ok, owner}
  defp validate_owner(_, _), do: refusal("ACTIVITY_CENSUS_OWNER")

  defp parse_window(%{"window" => %{"since" => since, "until" => until}}) do
    with {:ok, since, _} <- DateTime.from_iso8601(since),
         {:ok, until, _} <- DateTime.from_iso8601(until),
         :lt <- DateTime.compare(since, until) do
      {:ok, since, until}
    else
      _ -> refusal("ACTIVITY_CENSUS_WINDOW")
    end
  end

  defp parse_window(_), do: refusal("ACTIVITY_CENSUS_WINDOW")

  defp repositories(
         %{"reconciliation" => %{"union_repository_count" => count, "union_repositories" => repos}},
         owner
       )
       when is_integer(count) and is_list(repos) do
    with :ok <- ensure(Enum.all?(repos, &is_binary/1), "ACTIVITY_CENSUS_REPOSITORY_IDENTITY"),
         :ok <- ensure(length(repos) == count, "ACTIVITY_CENSUS_POPULATION_MISMATCH"),
         :ok <- ensure(length(Enum.uniq(repos)) == length(repos), "ACTIVITY_CENSUS_REPOSITORY_DUPLICATE"),
         :ok <- ensure(Enum.all?(repos, &String.starts_with?(&1, owner <> "/")), "ACTIVITY_CENSUS_REPOSITORY_SCOPE") do
      {:ok, Enum.sort(repos)}
    end
  end

  defp repositories(_, _), do: refusal("ACTIVITY_CENSUS_POPULATION")

  defp observe(client, client_opts, repositories, since, until) do
    Enum.reduce_while(repositories, {:ok, []}, fn repository, {:ok, acc} ->
      case client.(repository, since, until, client_opts) do
        {:ok, rows} when is_list(rows) ->
          case ledger(repository, rows, since, until) do
            {:ok, ledger} -> {:cont, {:ok, [ledger | acc]}}
            error -> {:halt, error}
          end

        {:error, reason} -> {:halt, {:error, to_string(reason)}}
        other -> {:halt, refusal("CI_RUN_CLIENT_CONTRACT", inspect(other))}
      end
    end)
    |> case do
      {:ok, ledgers} -> {:ok, Enum.reverse(ledgers)}
      error -> error
    end
  end

  defp ledger(repository, rows, since, until) do
    with {:ok, rows} <- exact_rows(rows, since, until),
         {:ok, rows} <- deduplicate(rows) do
      runs = rows |> Enum.map(&project/1) |> Enum.sort_by(& &1["identity"])
      completed = Enum.filter(runs, &(&1["status"] == "completed"))
      pending = Enum.reject(runs, &(&1["status"] == "completed"))
      failures = Enum.filter(completed, &(&1["conclusion"] in @failure_like))

      {:ok,
       %{
         "repository" => repository,
         "observed_run_count" => length(runs),
         "completed_run_count" => length(completed),
         "pending_run_count" => length(pending),
         "failure_like_run_count" => length(failures),
         "conclusion_counts" => completed |> Enum.map(&(&1["conclusion"] || "none")) |> Enum.frequencies(),
         "runs" => runs
       }}
    end
  end

  defp exact_rows(rows, since, until) do
    Enum.reduce_while(rows, {:ok, []}, fn row, {:ok, acc} ->
      case DateTime.from_iso8601(Map.get(row, "created_at", "")) do
        {:ok, created_at, _} ->
          if DateTime.compare(created_at, since) in [:eq, :gt] and DateTime.compare(created_at, until) == :lt,
            do: {:cont, {:ok, [row | acc]}},
            else: {:cont, {:ok, acc}}

        _ ->
          {:halt, refusal("CI_RUN_TIMESTAMP_INVALID")}
      end
    end)
    |> case do
      {:ok, rows} -> {:ok, Enum.reverse(rows)}
      error -> error
    end
  end

  defp deduplicate(rows) do
    Enum.reduce_while(rows, {:ok, %{}}, fn row, {:ok, acc} ->
      case identity(row) do
        {:ok, id} ->
          case Map.fetch(acc, id) do
            :error -> {:cont, {:ok, Map.put(acc, id, row)}}
            {:ok, ^row} -> {:cont, {:ok, acc}}
            {:ok, _} -> {:halt, refusal("CI_RUN_IDENTITY_CONFLICT", "identity=#{id}")}
          end

        error ->
          {:halt, error}
      end
    end)
    |> case do
      {:ok, by_id} -> {:ok, Map.values(by_id)}
      error -> error
    end
  end

  defp identity(%{"id" => id}) when is_integer(id), do: {:ok, "id:#{id}"}
  defp identity(%{"node_id" => id}) when is_binary(id) and id != "", do: {:ok, "node:#{id}"}
  defp identity(_), do: refusal("CI_RUN_IDENTITY_MISSING")

  defp project(row) do
    {:ok, id} = identity(row)

    Map.take(row, ~w(id node_id name event status conclusion created_at updated_at head_sha html_url))
    |> Map.put("identity", id)
  end

  defp observation(activity, owner, since, until, ledgers) do
    observed = where(ledgers, &(&1["observed_run_count"] > 0))
    without = where(ledgers, &(&1["observed_run_count"] == 0))
    failures = where(ledgers, &(&1["failure_like_run_count"] > 0))
    pending = where(ledgers, &(&1["pending_run_count"] > 0))
    total = length(ledgers)

    %{
      "schema" => @schema,
      "owner" => owner,
      "window" => %{"since" => iso_z(since), "until" => iso_z(until)},
      "upstream_activity_census" => %{
        "schema" => activity["schema"],
        "observation_digest" => get_in(activity, ["receipt", "observation_digest"])
      },
      "repositories" => ledgers,
      "summary" => %{
        "admitted_repository_count" => total,
        "repositories_with_observed_ci_runs" => length(observed),
        "repositories_with_observed_ci_run_names" => observed,
        "repositories_without_observed_ci_runs" => length(without),
        "repositories_without_observed_ci_run_names" => without,
        "repositories_with_failure_like_outcomes" => length(failures),
        "repositories_with_failure_like_outcome_names" => failures,
        "repositories_with_pending_runs" => length(pending),
        "repositories_with_pending_run_names" => pending,
        "observed_ci_repository_fraction" => "#{length(observed)}/#{total}"
      },
      "standing" => "PARTIAL_ALIVE",
      "claim_ceiling" => "OBSERVED_GITHUB_ACTIONS_OUTCOMES_FOR_ADMITTED_ACTIVITY_UNION",
      "exclusions" => [
        "non-GitHub CI providers",
        "local-only build and test execution",
        "required-check inference",
        "repository correctness inferred from CI success",
        "repositories absent from the upstream activity subject",
        "release, deployment, cloud actuation, and consequential DO"
      ]
    }
  end

  defp where(ledgers, predicate),
    do: ledgers |> Enum.filter(predicate) |> Enum.map(& &1["repository"]) |> Enum.sort()

  defp iso_z(value),
    do: value |> DateTime.truncate(:second) |> DateTime.to_iso8601() |> String.replace("+00:00", "Z")

  defp ensure(true, _), do: :ok
  defp ensure(false, code), do: refusal(code)

  defp refusal(code, detail \\ nil) do
    suffix = if detail in [nil, ""], do: "", else: " " <> to_string(detail)
    {:error, "REFUSED[#{code}]" <> suffix}
  end
end

defmodule ChatmanEcosystem.MeasurementDomain do
  @moduledoc false
  use Ash.Domain, extensions: [AshProjectMeasure], validate_config_inclusion?: false

  project_measure do
    github_actions do
      owner "seanchatmangpt"
      activity_census_path "../../.artifacts/activity-census/census.json"
      output_path "../../.artifacts/activity-census/ci-outcomes.json"
      token_env "GITHUB_TOKEN"
      api_url "https://api.github.com"
    end
  end
end
