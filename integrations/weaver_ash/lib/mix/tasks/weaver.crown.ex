defmodule Mix.Tasks.Weaver.Crown do
  @moduledoc """
  Runs the exact-subject Weaver capability crown through Ash.Reactor.

  DO-class loopback execution requires caller-supplied broker evidence:

      WEAVER_DO_AUTHORITY_SUBJECT=<exact git sha>
      WEAVER_DO_AUTHORITY_SCOPE=weaver.loopback
  """

  use Mix.Task

  @shortdoc "Runs Weaver live validation through Ash.Reactor"

  @switches [
    root: :string,
    repository: :string,
    subject_sha: :string,
    registry: :string,
    receipt_dir: :string,
    broker_subject: :string,
    broker_scope: :string
  ]

  @impl Mix.Task
  def run(argv) do
    Mix.Task.run("app.start")

    {opts, positional} = OptionParser.parse!(argv, strict: @switches)

    if positional != [] do
      Mix.raise("unexpected positional arguments: #{inspect(positional)}")
    end

    root = opts[:root] || default_root()
    subject_sha = opts[:subject_sha] || System.get_env("ECOSYSTEM_SUBJECT_SHA") || git_head!(root)
    repository = opts[:repository] || System.get_env("GITHUB_REPOSITORY") || "seanchatmangpt/chatman-ecosystem"
    registry = opts[:registry] || System.get_env("WEAVER_REGISTRY") || "telemetry/weaver"
    receipt_dir = opts[:receipt_dir] || System.get_env("WEAVER_RECEIPT_DIR") || "target/weaver-live"

    broker_subject =
      opts[:broker_subject] ||
        System.get_env("WEAVER_DO_AUTHORITY_SUBJECT") ||
        Mix.raise("REFUSED_MISSING_BROKER_SUBJECT")

    broker_scope =
      opts[:broker_scope] ||
        System.get_env("WEAVER_DO_AUTHORITY_SCOPE") ||
        Mix.raise("REFUSED_MISSING_BROKER_SCOPE")

    arguments = %{
      root: root,
      repository: repository,
      subject_sha: subject_sha,
      registry: registry,
      receipt_dir: receipt_dir,
      broker_subject: broker_subject,
      broker_scope: broker_scope
    }

    result =
      WeaverAsh.Control
      |> Ash.ActionInput.for_action(:crown, arguments)
      |> Ash.run_action(domain: WeaverAsh.Domain)

    case result do
      {:ok, receipt} ->
        IO.puts(Jason.encode!(receipt, pretty: true))

      {:error, error} ->
        Mix.raise("Weaver Ash.Reactor crown failed: #{Exception.format(:error, error, [])}")
    end
  end

  defp default_root do
    Path.expand("../../../../..", __DIR__)
  end

  defp git_head!(root) do
    case System.cmd("git", ["rev-parse", "HEAD"], cd: root, stderr_to_stdout: true) do
      {head, 0} -> String.trim(head)
      {output, code} -> Mix.raise("git rev-parse HEAD exited #{code}: #{output}")
    end
  end
end
