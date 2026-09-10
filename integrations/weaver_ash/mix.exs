defmodule WeaverAsh.MixProject do
  use Mix.Project

  def project do
    [
      app: :weaver_ash,
      version: "26.8.22",
      elixir: "~> 1.20",
      start_permanent: Mix.env() == :prod,
      consolidate_protocols: Mix.env() != :dev,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:logger, :crypto]
    ]
  end

  defp deps do
    [
      {:ash, "== 3.32.0"},
      {:reactor, "== 1.0.6"},
      {:jason, "~> 1.4"},
      {:sourceror, "~> 1.8", only: [:dev, :test]}
    ]
  end
end
