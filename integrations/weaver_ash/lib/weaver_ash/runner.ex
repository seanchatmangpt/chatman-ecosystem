defmodule WeaverAsh.Runner do
  @moduledoc """
  Bounded external Weaver executor used by Ash actions.

  This module never manufactures DO authority. It only admits broker evidence
  supplied by the caller and constrains that evidence to the exact subject and
  the local `weaver.loopback` scope used by the verification rail.
  """

  @required_capabilities [
    "check.future-v2-alpha-fence",
    "cli.help",
    "registry.help",
    "check.local",
    "check.git_exact_sha",
    "generate",
    "resolve.deprecated",
    "stats.json",
    "update-markdown",
    "json-schema.semconv-definition-v2",
    "diff.json",
    "package",
    "diagnostic.init",
    "completion.bash",
    "live-check.ecosystem",
    "live-check.otlp",
    "emit.loopback",
    "infer",
    "mcp",
    "serve.experimental"
  ]

  @ash_native_capabilities MapSet.new([
                             "live-check.ecosystem",
                             "live-check.otlp",
                             "emit.loopback"
                           ])

  @type refusal :: %{code: String.t(), detail: String.t()}

  @spec admit_subject(map()) :: {:ok, map()} | {:error, refusal()}
  def admit_subject(%{root: root, subject_sha: subject_sha}) do
    with :ok <- validate_sha(subject_sha),
         {:ok, head} <- command("git", ["rev-parse", "HEAD"], cd: root) do
      if String.trim(head) == subject_sha do
        {:ok,
         %{
           "subject" => "git:#{subject_sha}",
           "status" => "ALIVE",
           "executed" => true,
           "capability" => "ash.admit-exact-subject",
           "authority" => "SELECT",
           "exit_code" => 0,
           "detail" => "Ash admitted exact git subject before Reactor execution",
           "execution_plane" => "ash-reactor"
         }}
      else
        refused(
          "REFUSED_SUBJECT_MISMATCH",
          "expected #{subject_sha}, observed #{String.trim(head)}"
        )
      end
    end
  end

  @spec validate_broker(map()) :: :ok | {:error, refusal()}
  def validate_broker(%{
        subject_sha: subject_sha,
        broker_subject: broker_subject,
        broker_scope: broker_scope
      }) do
    cond do
      broker_subject != subject_sha ->
        refused(
          "REFUSED_DO_AUTHORITY_SUBJECT",
          "broker subject #{inspect(broker_subject)} does not match #{subject_sha}"
        )

      broker_scope != "weaver.loopback" ->
        refused(
          "REFUSED_DO_AUTHORITY_SCOPE",
          "broker scope must be exactly weaver.loopback"
        )

      true ->
        :ok
    end
  end

  @spec run_matrix(map()) :: {:ok, map()} | {:error, refusal()}
  def run_matrix(args) do
    with :ok <- validate_broker(args),
         {:ok, _output} <-
           command(
             "bash",
             ["scripts/weaver-live-matrix.sh"],
             cd: args.root,
             env: [
               {"ECOSYSTEM_SUBJECT_SHA", args.subject_sha},
               {"GITHUB_REPOSITORY", args.repository},
               {"WEAVER_REGISTRY", args.registry},
               {"WEAVER_RECEIPT_DIR", args.receipt_dir},
               {"WEAVER_DO_AUTHORITY_SUBJECT", args.broker_subject},
               {"WEAVER_DO_AUTHORITY_SCOPE", args.broker_scope}
             ],
             error_code: "BUILD_BROKEN_WEAVER_MATRIX"
           ),
         {:ok, receipt} <- read_json(receipt_path(args.root, args.receipt_dir)),
         :ok <- validate_matrix_identity(receipt, args.subject_sha) do
      {:ok, receipt}
    end
  end

  @spec live_check_stdin(map()) :: {:ok, map()} | {:error, refusal()}
  def live_check_stdin(args) do
    log_path = output_path(args.root, args.receipt_dir, "logs/live-check.ash.stdin.log")
    File.mkdir_p!(Path.dirname(log_path))

    script = """
    set -euo pipefail
    printf '%s\n' \
      "chatman.ecosystem.repository=${WEAVER_REPOSITORY}" \
      "chatman.ecosystem.subject.sha=${WEAVER_SUBJECT_SHA}" \
      "chatman.ecosystem.command=release.check-refs" \
      "chatman.ecosystem.result=ok" "" \
    | weaver registry live-check \
        -r "${WEAVER_REGISTRY}" \
        --v2 \
        --input-source stdin \
        --input-format text \
        --fail-on none \
        --output none
    """

    with {:ok, output} <-
           command(
             "bash",
             ["-lc", script],
             cd: args.root,
             env: [
               {"WEAVER_REPOSITORY", args.repository},
               {"WEAVER_SUBJECT_SHA", args.subject_sha},
               {"WEAVER_REGISTRY", args.registry}
             ],
             error_code: "BUILD_BROKEN_ASH_LIVE_CHECK_STDIN"
           ),
         :ok <- File.write(log_path, output) do
      {:ok,
       capability(
         "live-check.ecosystem",
         "SELECT",
         args.subject_sha,
         "Ash action + Ash.Reactor assessed the exact-subject release check through Weaver stdin"
       )}
    else
      {:error, reason} when is_atom(reason) ->
        refused("BUILD_BROKEN_RECEIPT_WRITE", inspect(reason))

      {:error, _reason} = error ->
        error
    end
  end

  @spec live_check_otlp(map()) :: {:ok, map()} | {:error, refusal()}
  def live_check_otlp(args) do
    log_path = output_path(args.root, args.receipt_dir, "logs/live-check.ash.otlp.log")
    File.mkdir_p!(Path.dirname(log_path))

    script = """
    set -euo pipefail
    live_pid=""
    cleanup() {
      if [ -n "${live_pid}" ]; then
        kill "${live_pid}" 2>/dev/null || true
      fi
    }
    trap cleanup EXIT

    weaver registry live-check \
      -r "${WEAVER_REGISTRY}" \
      --v2 \
      --input-source otlp \
      --otlp-grpc-address 127.0.0.1 \
      --otlp-grpc-port 15317 \
      --admin-port 15320 \
      --inactivity-timeout 4 \
      --fail-on none \
      --output none &
    live_pid=$!

    sleep 2

    weaver registry emit \
      -r "${WEAVER_REGISTRY}" \
      --v2 \
      --skip-policies \
      --endpoint http://127.0.0.1:15317

    wait "${live_pid}"
    live_pid=""
    trap - EXIT
    """

    with :ok <- validate_broker(args),
         {:ok, output} <-
           command(
             "bash",
             ["-lc", script],
             cd: args.root,
             env: [{"WEAVER_REGISTRY", args.registry}],
             error_code: "BUILD_BROKEN_ASH_LIVE_CHECK_OTLP"
           ),
         :ok <- File.write(log_path, output) do
      broker = %{
        "broker_subject" => args.broker_subject,
        "broker_scope" => args.broker_scope
      }

      {:ok,
       %{
         "capabilities" => [
           capability(
             "live-check.otlp",
             "SELECT",
             args.subject_sha,
             "Ash action + Ash.Reactor observed loopback OTLP live-check execution"
           ),
           Map.merge(
             capability(
               "emit.loopback",
               "DO",
               args.subject_sha,
               "Ash action admitted exact-subject loopback broker evidence before Weaver emit"
             ),
             broker
           )
         ]
       }}
    else
      {:error, reason} when is_atom(reason) ->
        refused("BUILD_BROKEN_RECEIPT_WRITE", inspect(reason))

      {:error, _reason} = error ->
        error
    end
  end

  @spec finalize_receipt(map()) :: {:ok, map()} | {:error, refusal()}
  def finalize_receipt(args) do
    capabilities =
      replace_native_capabilities(
        Map.get(args.matrix, "capabilities", []),
        args.stdin,
        Map.get(args.otlp, "capabilities", [])
      )

    with :ok <- validate_capabilities(capabilities, args.subject_sha, @required_capabilities) do
      receipt =
        args.matrix
        |> Map.put("subject", "git:#{args.subject_sha}")
        |> Map.put("capabilities", capabilities)
        |> Map.put("orchestrator", %{
          "framework" => "Ash.Reactor",
          "ash" => application_version(:ash),
          "reactor" => application_version(:reactor),
          "standing_owner" => "chatman-ecosystem constitution",
          "live_check_owner" => "WeaverAsh.Capability"
        })

      path = receipt_path(args.root, args.receipt_dir)
      encoded = Jason.encode!(receipt, pretty: true) <> "\n"
      digest = :crypto.hash(:sha256, encoded) |> Base.encode16(case: :lower)

      with :ok <- File.write(path, encoded),
           :ok <- File.write(output_path(args.root, args.receipt_dir, "receipt.sha256"), "#{digest}  receipt.json\n") do
        {:ok,
         %{
           "standing" => "ALIVE",
           "subject" => "git:#{args.subject_sha}",
           "receipt" => path,
           "sha256" => digest,
           "capability_count" => length(capabilities),
           "orchestrator" => "Ash.Reactor"
         }}
      else
        {:error, reason} ->
          refused("BUILD_BROKEN_RECEIPT_WRITE", inspect(reason))
      end
    end
  end

  @spec replace_native_capabilities([map()], map(), [map()]) :: [map()]
  def replace_native_capabilities(matrix_capabilities, stdin_capability, otlp_capabilities) do
    matrix_capabilities
    |> Enum.reject(fn capability ->
      MapSet.member?(@ash_native_capabilities, Map.get(capability, "capability"))
    end)
    |> Kernel.++([stdin_capability | otlp_capabilities])
  end

  @spec validate_capabilities([map()], String.t(), [String.t()]) ::
          :ok | {:error, refusal()}
  def validate_capabilities(capabilities, subject_sha, required_names) do
    subject = "git:#{subject_sha}"
    names = MapSet.new(Enum.map(capabilities, &Map.get(&1, "capability")))

    cond do
      missing = Enum.find(required_names, &(not MapSet.member?(names, &1))) ->
        refused("REFUSED_INCOMPLETE_CAPABILITY_CROWN", "missing #{missing}")

      bad_subject =
          Enum.find(capabilities, fn capability ->
            Map.get(capability, "subject") != subject
          end) ->
        refused(
          "REFUSED_RECEIPT_SUBJECT_MISMATCH",
          "#{Map.get(bad_subject, "capability")} names #{inspect(Map.get(bad_subject, "subject"))}"
        )

      not_executed =
          Enum.find(capabilities, fn capability ->
            Map.get(capability, "executed") != true
          end) ->
        refused(
          "REFUSED_UNEXECUTED_CAPABILITY",
          "#{Map.get(not_executed, "capability")} was not executed"
        )

      broken =
          Enum.find(capabilities, fn capability ->
            Map.get(capability, "status") in ["BUILD_BROKEN", "BLOCKED", "UNKNOWN"]
          end) ->
        refused(
          "REFUSED_BROKEN_CAPABILITY_CROWN",
          "#{Map.get(broken, "capability")} is #{Map.get(broken, "status")}"
        )

      true ->
        :ok
    end
  end

  defp validate_matrix_identity(receipt, subject_sha) do
    if Map.get(receipt, "subject") == "git:#{subject_sha}" do
      :ok
    else
      refused(
        "REFUSED_MATRIX_SUBJECT_MISMATCH",
        "matrix receipt does not name git:#{subject_sha}"
      )
    end
  end

  defp validate_sha(subject_sha) do
    if is_binary(subject_sha) and Regex.match?(~r/\A[0-9a-f]{40}\z/, subject_sha) do
      :ok
    else
      refused(
        "REFUSED_SUBJECT_SHA",
        "subject SHA must be exactly 40 lowercase hexadecimal characters"
      )
    end
  end

  defp capability(name, authority, subject_sha, detail) do
    %{
      "capability" => name,
      "authority" => authority,
      "status" => "ALIVE",
      "executed" => true,
      "exit_code" => 0,
      "subject" => "git:#{subject_sha}",
      "detail" => detail,
      "execution_plane" => "ash-reactor"
    }
  end

  defp command(program, argv, opts) do
    error_code = Keyword.get(opts, :error_code, "BUILD_BROKEN_COMMAND")
    system_opts = Keyword.drop(opts, [:error_code])

    try do
      case System.cmd(program, argv, Keyword.put(system_opts, :stderr_to_stdout, true)) do
        {output, 0} ->
          {:ok, output}

        {output, exit_code} ->
          refused(
            error_code,
            "#{program} exited #{exit_code}: #{String.slice(output, 0, 4_000)}"
          )
      end
    rescue
      error ->
        refused(error_code, Exception.message(error))
    end
  end

  defp read_json(path) do
    with {:ok, body} <- File.read(path),
         {:ok, value} <- Jason.decode(body) do
      {:ok, value}
    else
      {:error, reason} ->
        refused("BUILD_BROKEN_RECEIPT_READ", "#{path}: #{inspect(reason)}")
    end
  end

  defp receipt_path(root, receipt_dir) do
    output_path(root, receipt_dir, "receipt.json")
  end

  defp output_path(root, receipt_dir, suffix) do
    receipt_dir
    |> absolute_from(root)
    |> Path.join(suffix)
  end

  defp absolute_from(path, root) do
    if Path.type(path) == :absolute, do: path, else: Path.expand(path, root)
  end

  defp application_version(application) do
    application
    |> Application.spec(:vsn)
    |> to_string()
  end

  defp refused(code, detail) do
    {:error, %{code: code, detail: detail}}
  end
end
