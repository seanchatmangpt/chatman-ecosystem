defmodule AshProjectMeasureTest do
  use ExUnit.Case, async: true

  defmodule TestDomain do
    use Ash.Domain, extensions: [AshProjectMeasure]

    project_measure do
      github_actions do
        owner "seanchatmangpt"
        activity_census_path "tmp/activity.json"
        output_path "tmp/ci.json"
        token_env "TEST_GITHUB_TOKEN"
        api_url "https://example.invalid"
      end
    end
  end

  test "domain extension exposes project measurement configuration" do
    assert AshProjectMeasure.Info.config(TestDomain) == %{
             owner: "seanchatmangpt",
             activity_census_path: "tmp/activity.json",
             output_path: "tmp/ci.json",
             token_env: "TEST_GITHUB_TOKEN",
             api_url: "https://example.invalid"
           }
  end

  test "canonical receipt digest matches the predecessor Python rail" do
    observation = %{
      "schema" => "chatman.portfolio-activity-census/2",
      "owner" => "seanchatmangpt",
      "window" => %{
        "since" => "2026-08-14T22:00:00Z",
        "until" => "2026-08-21T22:00:00Z"
      },
      "reconciliation" => %{
        "union_repository_count" => 2,
        "union_repositories" => ["seanchatmangpt/a", "seanchatmangpt/b"]
      },
      "standing" => "PARTIAL_ALIVE"
    }

    assert AshProjectMeasure.Receipt.digest(observation) ==
             "778bf50a7c3d286ff0d1b749d52c4ed39f54052381671016728f8ee92ed5e3b1"
  end
end

defmodule AshProjectMeasure.CensusTest do
  use ExUnit.Case, async: false

  alias AshProjectMeasure.{Census, Receipt}

  defmodule FakeClient do
    def list_workflow_runs(repository, _since, _until, _opts) do
      {:ok, Process.get({__MODULE__, repository}, [])}
    end
  end

  setup do
    on_exit(fn ->
      Enum.each(["a", "b"], fn name ->
        Process.delete({FakeClient, "seanchatmangpt/#{name}"})
      end)
    end)

    :ok
  end

  test "classifies exact-window completed, pending, failure-like, and no-observed-CI repositories" do
    Process.put(
      {FakeClient, "seanchatmangpt/a"},
      [
        run(1, "2026-08-20T12:00:00Z", "completed", "success"),
        run(2, "2026-08-20T13:00:00Z", "completed", "failure"),
        run(3, "2026-08-20T14:00:00Z", "in_progress", nil),
        run(4, "2026-08-21T22:00:00Z", "completed", "failure")
      ]
    )

    assert {:ok, payload} =
             Census.build(activity_fixture(), config(),
               client: &FakeClient.list_workflow_runs/4,
               client_opts: []
             )

    assert payload["summary"]["admitted_repository_count"] == 2
    assert payload["summary"]["repositories_with_observed_ci_runs"] == 1
    assert payload["summary"]["repositories_without_observed_ci_runs"] == 1
    assert payload["summary"]["repositories_with_failure_like_outcomes"] == 1
    assert payload["summary"]["repositories_with_pending_runs"] == 1

    [a, b] = payload["repositories"]
    assert a["repository"] == "seanchatmangpt/a"
    assert a["observed_run_count"] == 3
    assert a["completed_run_count"] == 2
    assert a["pending_run_count"] == 1
    assert a["failure_like_run_count"] == 1
    assert b["repository"] == "seanchatmangpt/b"
    assert b["observed_run_count"] == 0
    assert Receipt.verify(payload)
  end

  test "tampered upstream activity receipt is refused" do
    tampered = put_in(activity_fixture(), ["window", "until"], "2026-08-22T22:00:00Z")

    assert {:error, "REFUSED[ACTIVITY_CENSUS_RECEIPT]"} =
             Census.build(tampered, config(), client: &FakeClient.list_workflow_runs/4)
  end

  test "foreign repository in admitted population is refused" do
    activity =
      activity_fixture()
      |> Map.put("reconciliation", %{
        "union_repository_count" => 1,
        "union_repositories" => ["someone-else/repo"]
      })
      |> re_receipt()

    assert {:error, "REFUSED[ACTIVITY_CENSUS_REPOSITORY_SCOPE]"} =
             Census.build(activity, config(), client: &FakeClient.list_workflow_runs/4)
  end

  test "population count mismatch is refused instead of fabricating a denominator" do
    activity =
      activity_fixture()
      |> Map.put("reconciliation", %{
        "union_repository_count" => 3,
        "union_repositories" => ["seanchatmangpt/a", "seanchatmangpt/b"]
      })
      |> re_receipt()

    assert {:error, "REFUSED[ACTIVITY_CENSUS_POPULATION_MISMATCH]"} =
             Census.build(activity, config(), client: &FakeClient.list_workflow_runs/4)
  end

  test "conflicting duplicate workflow-run identity is refused" do
    Process.put(
      {FakeClient, "seanchatmangpt/a"},
      [
        run(1, "2026-08-20T12:00:00Z", "completed", "success"),
        run(1, "2026-08-20T12:00:00Z", "completed", "failure")
      ]
    )

    assert {:error, "REFUSED[CI_RUN_IDENTITY_CONFLICT] identity=id:1"} =
             Census.build(activity_fixture(), config(), client: &FakeClient.list_workflow_runs/4)
  end

  test "tampered CI outcome receipt fails replay verification" do
    assert {:ok, payload} =
             Census.build(activity_fixture(), config(), client: &FakeClient.list_workflow_runs/4)

    tampered = put_in(payload, ["summary", "admitted_repository_count"], 999)
    refute Receipt.verify(tampered)
  end

  defp config do
    %{
      owner: "seanchatmangpt",
      activity_census_path: "unused.json",
      output_path: "unused.json",
      token_env: "GITHUB_TOKEN",
      api_url: "https://api.github.com"
    }
  end

  defp activity_fixture do
    observation = %{
      "schema" => "chatman.portfolio-activity-census/2",
      "owner" => "seanchatmangpt",
      "window" => %{
        "since" => "2026-08-14T22:00:00Z",
        "until" => "2026-08-21T22:00:00Z"
      },
      "reconciliation" => %{
        "union_repository_count" => 2,
        "union_repositories" => ["seanchatmangpt/a", "seanchatmangpt/b"]
      },
      "standing" => "PARTIAL_ALIVE"
    }

    Map.put(observation, "receipt", %{
      "algorithm" => "sha256",
      "observation_digest" =>
        "778bf50a7c3d286ff0d1b749d52c4ed39f54052381671016728f8ee92ed5e3b1",
      "replay" => "python predecessor receipt"
    })
  end

  defp re_receipt(payload) do
    payload |> Map.delete("receipt") |> Receipt.attach()
  end

  defp run(id, created_at, status, conclusion) do
    %{
      "id" => id,
      "node_id" => "NODE#{id}",
      "name" => "ci",
      "event" => "pull_request",
      "status" => status,
      "conclusion" => conclusion,
      "created_at" => created_at,
      "updated_at" => created_at,
      "head_sha" => String.duplicate(Integer.to_string(id), 40),
      "html_url" => "https://github.com/seanchatmangpt/a/actions/runs/#{id}"
    }
  end
end
