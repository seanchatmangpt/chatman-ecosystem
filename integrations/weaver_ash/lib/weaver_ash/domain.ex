defmodule WeaverAsh.Domain do
  @moduledoc """
  Ash domain for the Weaver composition adapter.

  The domain exposes Weaver verification as Ash actions while leaving
  constitutional identity, authority, standing, and receipt law outside the
  framework.
  """

  use Ash.Domain, otp_app: :weaver_ash

  resources do
    resource WeaverAsh.Control
    resource WeaverAsh.Capability
  end
end
