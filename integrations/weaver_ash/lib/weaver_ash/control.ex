defmodule WeaverAsh.Control do
  @moduledoc """
  Public Ash entrypoint for the exact-subject Weaver capability crown.

  The generic action is intentionally implemented by an `Ash.Reactor`, which
  makes the complete crown available through normal Ash action semantics.
  """

  use Ash.Resource, domain: WeaverAsh.Domain

  actions do
    action :crown, :map do
      argument :root, :string, allow_nil?: false
      argument :repository, :string, allow_nil?: false
      argument :subject_sha, :string, allow_nil?: false
      argument :registry, :string, allow_nil?: false
      argument :receipt_dir, :string, allow_nil?: false
      argument :broker_subject, :string, allow_nil?: false
      argument :broker_scope, :string, allow_nil?: false

      run {WeaverAsh.CrownReactor, async?: false}
    end
  end
end
