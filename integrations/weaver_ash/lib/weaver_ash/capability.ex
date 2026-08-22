defmodule WeaverAsh.Capability do
  @moduledoc """
  Ash action surface for Weaver capability execution.

  Each action is side-effect explicit. The two live-check actions are native
  Ash actions; the compatibility matrix remains an external Weaver provider
  invoked through this resource rather than an ambient shell crown.
  """

  use Ash.Resource, domain: WeaverAsh.Domain

  alias WeaverAsh.Runner

  actions do
    action :admit_subject, :map do
      argument :root, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false

      run fn input, _context ->
        Runner.admit_subject(input.arguments)
      end
    end

    action :run_matrix, :map do
      argument :root, :string, allow_nil?: false
      argument :repository, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false
      argument :registry, :string, allow_nil?: false
      argument :receipt_dir, :string, allow_nil?: false
      argument :broker_subject, :string, allow_nil?: false
      argument :broker_scope, :string, allow_nil?: false

      run fn input, _context ->
        Runner.run_matrix(input.arguments)
      end
    end

    action :live_check_stdin, :map do
      argument :root, :string, allow_nil?: false
      argument :repository, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false
      argument :registry, :string, allow_nil?: false
      argument :receipt_dir, :string, allow_nil?: false

      run fn input, _context ->
        Runner.live_check_stdin(input.arguments)
      end
    end

    action :live_check_otlp, :map do
      argument :root, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false
      argument :registry, :string, allow_nil?: false
      argument :receipt_dir, :string, allow_nil?: false
      argument :broker_subject, :string, allow_nil?: false
      argument :broker_scope, :string, allow_nil?: false

      run fn input, _context ->
        Runner.live_check_otlp(input.arguments)
      end
    end

    action :finalize_receipt, :map do
      argument :root, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false
      argument :receipt_dir, :string, allow_nil?: false
      argument :matrix, :map, allow_nil?: false
      argument :stdin, :map, allow_nil?: false
      argument :otlp, :map, allow_nil?: false

      run fn input, _context ->
        Runner.finalize_receipt(input.arguments)
      end
    end
  end
end
