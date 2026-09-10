defmodule AshProjectMeasure.MixProject do
  use Mix.Project

  def project do
    [
      app: :ash_project_measure,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      extra_applications: [:crypto, :inets, :logger, :ssl]
    ]
  end

  defp deps do
    [
      {:ash, "~> 3.30"},
      {:jason, "~> 1.4"}
    ]
  end
end
