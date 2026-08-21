"""Real regression test for FMEA RPN=576 (Severity=8 x Occurrence=8 x Detection=9):

apply_sparql_bridge_extension() used to unconditionally wire an `alias
Xaas.Operations.<Class>` plus an `Ash.read(<Class>)` call into the live
Xaas.SparqlBridge.to_turtle/0 monitor function -- on every invocation, including the
documented default (non---deploy) path -- with no check that the corresponding Ash
resource .ex module actually existed on disk yet. Since that module is only generated
(via `ggen sync run`) and copied into the real xaas checkout under --deploy, every
default run left the live to_turtle/0 referencing a module that did not exist,
crashing `Ash.read/1` on the next real invocation.

Chicago style throughout: this test runs the real add_connector.py as a real
subprocess against a real temporary directory tree standing in for the real ~/xaas
checkout (via the XAAS_ROOT env var the fix introduced), and asserts on real,
resulting file state -- not on mocked calls or interactions. No unittest.mock,
Mock(), MagicMock(), patch(), or monkeypatch anywhere in this file.

Uses the `--backfill-bridge=<tool>` entry point deliberately: it exercises
apply_sparql_bridge_extension() directly without requiring the real, separate
clap-noun-verb-any manifest (MANIFEST_PATH), which is out of this repo's scope.
"""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent / "add_connector.py"

# A fixture sparql_bridge.ex: the real production file's structure (same anchors
# apply_sparql_bridge_extension() matches against), captured verbatim from
# ~/xaas/lib/xaas/sparql_bridge.ex, trimmed to what the anchors need but with every
# byte of the matched regions preserved exactly.
FIXTURE_BRIDGE = '''defmodule Xaas.SparqlBridge do
  @moduledoc """
  Real Monitor substrate for a MAPE-K loop.
  """

  alias Xaas.Operations.AutofdePlannerCandidate
  alias Xaas.Operations.AutofdePlannerCatalog
  alias Xaas.Operations.AutofdePlannerMatch

  @prefix "https://xaas.dev/ontology/autofde-monitor#"

  @spec to_turtle() :: String.t()
  def to_turtle do
    {:ok, candidates} = Ash.read(AutofdePlannerCandidate)
    {:ok, catalog_requests} = Ash.read(AutofdePlannerCatalog)
    {:ok, match_requests} = Ash.read(AutofdePlannerMatch)

    header = """
    @prefix aacm: <#{@prefix}> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    """

    body =
      (Enum.map(candidates, &candidate_to_turtle/1) ++
         Enum.map(catalog_requests, &catalog_to_turtle/1) ++
         Enum.map(match_requests, &match_to_turtle/1))
      |> Enum.join("\\n")

    header <> body
  end

  @spec match_to_turtle() :: String.t()
  def match_to_turtle do
    {:ok, rows} = Ash.read(AutofdePlannerMatch)
    turtle_document(Enum.map(rows, &match_to_turtle/1))
  end

  defp turtle_document(bodies) do
    header = """
    @prefix aacm: <#{@prefix}> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    """

    header <> Enum.join(bodies, "\\n")
  end

  defp candidate_to_turtle(%AutofdePlannerCandidate{} = row) do
    row
  end

  defp catalog_to_turtle(%AutofdePlannerCatalog{} = row) do
    row
  end

  defp match_to_turtle(%AutofdePlannerMatch{} = row) do
    subject = "aacm:PlannerMatchRequest_#{row.id}"

    render_individual(subject, [
      {"a", "aacm:PlannerMatchRequest"},
      {"aacm:query", turtle_string(row.query)},
      {"aacm:trajectorySha256", turtle_maybe_string(row.trajectory_sha256)},
      {"aacm:requestedAt", turtle_maybe_datetime(row.requested_at)}
    ])
  end

  defp render_individual(subject, lines) do
    subject
  end
end
'''

SHORT_NAME = "cache-evict"  # not a real connector; a fresh name only used by this test
CLASS_NAME = "AutofdePlannerCacheEvict"
OUTPUT_REL_PATH = "lib/xaas/operations/autofde_planner_cache_evict.ex"


def _make_fake_xaas(tmp_path: Path) -> Path:
    xaas_root = tmp_path / "xaas_root"
    bridge_path = xaas_root / "lib" / "xaas" / "sparql_bridge.ex"
    bridge_path.parent.mkdir(parents=True, exist_ok=True)
    bridge_path.write_text(FIXTURE_BRIDGE)
    return xaas_root


def _run_backfill(xaas_root: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "XAAS_ROOT": str(xaas_root)}
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), f"--backfill-bridge={SHORT_NAME}"],
        capture_output=True,
        text=True,
        env=env,
    )


def test_backfill_refuses_and_leaves_bridge_untouched_when_module_missing(tmp_path):
    """FMEA RPN=576 regression: wiring must be refused, with a non-zero real exit
    code, and sparql_bridge.ex must be byte-for-byte unchanged, when the real Ash
    resource module does not exist yet in the xaas checkout. This is the exact
    dangling-reference window the FMEA found: without this guard, the alias +
    Ash.read call would have been wired in regardless."""
    xaas_root = _make_fake_xaas(tmp_path)
    bridge_path = xaas_root / "lib" / "xaas" / "sparql_bridge.ex"
    before = bridge_path.read_text()

    # Precondition for the scenario under test: the Ash resource module genuinely
    # does not exist anywhere in the fake xaas checkout yet.
    assert not (xaas_root / OUTPUT_REL_PATH).exists()

    result = _run_backfill(xaas_root)

    assert result.returncode == 1, (
        f"expected a real non-zero exit code when the module is missing, got "
        f"{result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "REFUSED" in result.stderr
    assert "FMEA RPN=576" in result.stderr

    after = bridge_path.read_text()
    assert after == before, "sparql_bridge.ex must be left byte-for-byte untouched"
    assert f"alias Xaas.Operations.{CLASS_NAME}" not in after
    assert f"Ash.read({CLASS_NAME})" not in after


def test_backfill_wires_bridge_once_module_actually_exists(tmp_path):
    """Confirms the guard does not regress the legitimate case: once the real Ash
    resource module exists on disk (the state --deploy produces before it now calls
    apply_sparql_bridge_extension()), backfill wiring proceeds and succeeds with a
    real, verifiable exit code and real file content."""
    xaas_root = _make_fake_xaas(tmp_path)
    module_path = xaas_root / OUTPUT_REL_PATH
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text("defmodule Xaas.Operations.AutofdePlannerCacheEvict do\nend\n")

    result = _run_backfill(xaas_root)

    assert result.returncode == 0, (
        f"expected success once the module exists, got {result.returncode}\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )

    bridge_text = (xaas_root / "lib" / "xaas" / "sparql_bridge.ex").read_text()
    assert f"alias Xaas.Operations.{CLASS_NAME}" in bridge_text
    assert f"Ash.read({CLASS_NAME})" in bridge_text
    assert "def cache_evict_to_turtle do" in bridge_text
    assert "defp cache_evict_row_to_turtle(%AutofdePlannerCacheEvict{} = row) do" in bridge_text


def test_running_backfill_twice_is_idempotent_once_module_exists(tmp_path):
    """Real state-based check that a second backfill run (module already wired) is a
    real no-op -- exit 0, file unchanged the second time -- not a duplicate wiring."""
    xaas_root = _make_fake_xaas(tmp_path)
    module_path = xaas_root / OUTPUT_REL_PATH
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text("defmodule Xaas.Operations.AutofdePlannerCacheEvict do\nend\n")

    first = _run_backfill(xaas_root)
    assert first.returncode == 0
    bridge_text_after_first = (xaas_root / "lib" / "xaas" / "sparql_bridge.ex").read_text()

    second = _run_backfill(xaas_root)
    assert second.returncode == 0
    bridge_text_after_second = (xaas_root / "lib" / "xaas" / "sparql_bridge.ex").read_text()

    assert bridge_text_after_second == bridge_text_after_first
    assert "OK: sparql_bridge.ex already covers" in second.stdout
