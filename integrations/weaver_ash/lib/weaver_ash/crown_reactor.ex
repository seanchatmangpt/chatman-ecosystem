defmodule WeaverAsh.CrownReactor do
  @moduledoc """
  Exact-subject Weaver crown expressed as an Ash.Reactor saga.

  The graph is deliberately sequential at consequential boundaries: exact
  subject admission precedes compatibility execution; successful compatibility
  execution precedes native stdin live-check; the loopback OTLP edge requires
  explicit broker evidence; only then can the receipt be finalized.
  """

  use Ash.Reactor

  ash do
    default_domain WeaverAsh.Domain
  end

  input :root
  input :repository
  input :subject_sha
  input :registry
  input :receipt_dir
  input :broker_subject
  input :broker_scope

  action :admit_subject, WeaverAsh.Capability, :admit_subject do
    inputs %{
      root: input(:root),
      subject_sha: input(:subject_sha)
    }
  end

  action :compatibility_matrix, WeaverAsh.Capability, :run_matrix do
    wait_for :admit_subject

    inputs %{
      root: input(:root),
      repository: input(:repository),
      subject_sha: input(:subject_sha),
      registry: input(:registry),
      receipt_dir: input(:receipt_dir),
      broker_subject: input(:broker_subject),
      broker_scope: input(:broker_scope)
    }
  end

  action :live_check_stdin, WeaverAsh.Capability, :live_check_stdin do
    wait_for :compatibility_matrix

    inputs %{
      root: input(:root),
      repository: input(:repository),
      subject_sha: input(:subject_sha),
      registry: input(:registry),
      receipt_dir: input(:receipt_dir)
    }
  end

  action :live_check_otlp, WeaverAsh.Capability, :live_check_otlp do
    wait_for :live_check_stdin

    inputs %{
      root: input(:root),
      subject_sha: input(:subject_sha),
      registry: input(:registry),
      receipt_dir: input(:receipt_dir),
      broker_subject: input(:broker_subject),
      broker_scope: input(:broker_scope)
    }
  end

  action :finalize_receipt, WeaverAsh.Capability, :finalize_receipt do
    inputs %{
      root: input(:root),
      subject_sha: input(:subject_sha),
      receipt_dir: input(:receipt_dir),
      matrix: result(:compatibility_matrix),
      stdin: result(:live_check_stdin),
      otlp: result(:live_check_otlp)
    }
  end

  return :finalize_receipt
end
