defmodule WeaverAshTest do
  use ExUnit.Case, async: true

  alias WeaverAsh.Runner

  @sha String.duplicate("a", 40)

  test "generic Ash action is implemented by the crown Reactor" do
    action = Ash.Resource.Info.action(WeaverAsh.Control, :crown)

    assert action.name == :crown
    assert action.type == :action
    assert inspect(action.run) =~ "WeaverAsh.CrownReactor"
  end

  test "subject admission refuses non-exact SHA identities" do
    assert {:error, %{code: "REFUSED_SUBJECT_SHA"}} =
             Runner.admit_subject(%{root: ".", subject_sha: "not-a-sha"})
  end

  test "DO authority is exact-subject and loopback scoped" do
    assert :ok =
             Runner.validate_broker(%{
               subject_sha: @sha,
               broker_subject: @sha,
               broker_scope: "weaver.loopback"
             })

    assert {:error, %{code: "REFUSED_DO_AUTHORITY_SUBJECT"}} =
             Runner.validate_broker(%{
               subject_sha: @sha,
               broker_subject: String.duplicate("b", 40),
               broker_scope: "weaver.loopback"
             })

    assert {:error, %{code: "REFUSED_DO_AUTHORITY_SCOPE"}} =
             Runner.validate_broker(%{
               subject_sha: @sha,
               broker_subject: @sha,
               broker_scope: "production"
             })
  end

  test "native Ash live-check receipts replace compatibility-shell crowns" do
    shell = [
      capability("cli.help"),
      capability("live-check.ecosystem"),
      capability("live-check.otlp"),
      capability("emit.loopback")
    ]

    stdin = capability("live-check.ecosystem") |> Map.put("execution_plane", "ash-reactor")

    otlp = [
      capability("live-check.otlp") |> Map.put("execution_plane", "ash-reactor"),
      capability("emit.loopback") |> Map.put("execution_plane", "ash-reactor")
    ]

    result = Runner.replace_native_capabilities(shell, stdin, otlp)

    assert Enum.count(result, &(&1["capability"] == "live-check.ecosystem")) == 1
    assert Enum.count(result, &(&1["capability"] == "live-check.otlp")) == 1
    assert Enum.count(result, &(&1["capability"] == "emit.loopback")) == 1

    assert Enum.all?(
             Enum.filter(
               result,
               &(&1["capability"] in [
                   "live-check.ecosystem",
                   "live-check.otlp",
                   "emit.loopback"
                 ])
             ),
             &(&1["execution_plane"] == "ash-reactor")
           )
  end

  test "receipt validation refuses missing, stale, and unexecuted required edges" do
    required = ["one", "two"]

    assert {:error, %{code: "REFUSED_INCOMPLETE_CAPABILITY_CROWN"}} =
             Runner.validate_capabilities([capability("one")], @sha, required)

    stale = [
      capability("one"),
      capability("two")
      |> Map.put("subject", "git:" <> String.duplicate("b", 40))
    ]

    assert {:error, %{code: "REFUSED_RECEIPT_SUBJECT_MISMATCH"}} =
             Runner.validate_capabilities(stale, @sha, required)

    unexecuted = [
      capability("one"),
      capability("two") |> Map.put("executed", false)
    ]

    assert {:error, %{code: "REFUSED_UNEXECUTED_CAPABILITY"}} =
             Runner.validate_capabilities(unexecuted, @sha, required)
  end

  defp capability(name) do
    %{
      "capability" => name,
      "authority" => "SELECT",
      "status" => "ALIVE",
      "executed" => true,
      "exit_code" => 0,
      "subject" => "git:#{@sha}",
      "detail" => "test"
    }
  end
end
