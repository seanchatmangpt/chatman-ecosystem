defmodule WeaverAsh.Domain do
  @moduledoc """
  Ash domain for the Weaver composition adapter.

  The domain exposes Weaver verification as idiomatic Ash code interfaces while
  leaving constitutional identity, authority, standing, and receipt law outside
  the framework.
  """

  use Ash.Domain, otp_app: :weaver_ash

  resources do
    resource WeaverAsh.Control do
      define :crown,
        action: :crown,
        args: [
          :root,
          :repository,
          :subject_sha,
          :registry,
          :receipt_dir,
          :broker_subject,
          :broker_scope
        ]
    end

    resource WeaverAsh.Capability do
      define :admit_subject, action: :admit_subject, args: [:root, :subject_sha]

      define :run_matrix,
        action: :run_matrix,
        args: [
          :root,
          :repository,
          :subject_sha,
          :registry,
          :receipt_dir,
          :broker_subject,
          :broker_scope
        ]

      define :live_check_stdin,
        action: :live_check_stdin,
        args: [:root, :repository, :subject_sha, :registry, :receipt_dir]

      define :live_check_otlp,
        action: :live_check_otlp,
        args: [
          :root,
          :subject_sha,
          :registry,
          :receipt_dir,
          :broker_subject,
          :broker_scope
        ]

      define :finalize_receipt,
        action: :finalize_receipt,
        args: [:root, :subject_sha, :receipt_dir, :matrix, :stdin, :otlp]
    end
  end
end
