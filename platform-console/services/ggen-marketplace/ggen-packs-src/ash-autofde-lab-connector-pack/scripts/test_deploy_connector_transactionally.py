"""Chicago-style regression tests for transactional connector deployment.

The tests copy the real scripts into a real temporary pack, run the wrapper and child
as real subprocesses, and assert on resulting bytes. No mocks, patches, monkeypatches,
or fabricated interaction assertions are used.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REAL_SCRIPTS_DIR = Path(__file__).resolve().parent
TOOL_NAME = "fabric__transaction-test"
SHORT_NAME = "transaction-test"
OUTPUT_REL = Path("lib/xaas/operations/autofde_planner_transaction_test.ex")
GENERATED_BYTES = b"defmodule Xaas.Operations.AutofdePlannerTransactionTest do\nend\n"
PREEXISTING_BYTES = b"# operator-owned preexisting bytes\n"

FIXTURE_MANIFEST = {
    "commands": [
        {
            "path": ["fabric", "transaction-test"],
            "about": "Transactional deployment regression fixture.",
            "arguments": [],
        }
    ]
}

BASE_ONTOLOGY = """@prefix aac: <https://ggen.dev/ontology/ash-autofde-lab-connector#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

aac:AshConnector a rdfs:Class .
"""

SUCCESS_BRIDGE = """defmodule Xaas.SparqlBridge do
  alias Xaas.Operations.AutofdePlannerMatch

  def to_turtle do
    {:ok, match_requests} = Ash.read(AutofdePlannerMatch)

    header = \"\"\"
    @prefix aacm: <https://xaas.dev/ontology/autofde-monitor#> .
    \"\"\"

    body =
      (Enum.map(match_requests, &match_to_turtle/1))
      |> Enum.join(\"\\n\")

    header <> body
  end

  def match_to_turtle do
    {:ok, rows} = Ash.read(AutofdePlannerMatch)
    turtle_document(Enum.map(rows, &match_to_turtle/1))
  end

  defp match_to_turtle(%AutofdePlannerMatch{} = row) do
    subject = \"aacm:PlannerMatchRequest_#{row.id}\"

    render_individual(subject, [
      {\"a\", \"aacm:PlannerMatchRequest\"},
      {\"aacm:query\", turtle_string(row.query)},
      {\"aacm:trajectorySha256\", turtle_maybe_string(row.trajectory_sha256)},
      {\"aacm:requestedAt\", turtle_maybe_datetime(row.requested_at)}
    ])
  end
end
"""

BROKEN_BRIDGE = """defmodule Xaas.SparqlBridge do
  # Deliberately lacks the generator's structural anchors.
end
"""


def _make_fixture(tmp_path: Path, bridge_text: str) -> tuple[Path, Path, Path]:
    pack_dir = tmp_path / "pack"
    scripts_dir = pack_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    for name in ("add_connector.py", "deploy_connector_transactionally.py"):
        (scripts_dir / name).write_text((REAL_SCRIPTS_DIR / name).read_text())
    (pack_dir / "ontology.ttl").write_text(BASE_ONTOLOGY)

    manifest = tmp_path / "cnv-any.json"
    manifest.write_text(json.dumps(FIXTURE_MANIFEST))

    xaas_root = tmp_path / "xaas"
    bridge = xaas_root / "lib" / "xaas" / "sparql_bridge.ex"
    bridge.parent.mkdir(parents=True)
    bridge.write_text(bridge_text)
    return pack_dir, manifest, xaas_root


def _generated_target(pack_dir: Path) -> Path:
    return pack_dir / OUTPUT_REL


def _ggen_override(pack_dir: Path) -> str:
    target = _generated_target(pack_dir)
    code = (
        "from pathlib import Path; "
        f"p=Path({str(target)!r}); p.parent.mkdir(parents=True, exist_ok=True); "
        f"p.write_bytes({GENERATED_BYTES!r})"
    )
    return json.dumps([sys.executable, "-c", code])


def _run(pack_dir: Path, manifest: Path, xaas_root: Path) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "CNV_ANY_MANIFEST_PATH": str(manifest),
        "XAAS_ROOT": str(xaas_root),
        "GGEN_SYNC_CMD_OVERRIDE": _ggen_override(pack_dir),
    }
    return subprocess.run(
        [
            sys.executable,
            str(pack_dir / "scripts" / "deploy_connector_transactionally.py"),
            TOOL_NAME,
        ],
        capture_output=True,
        text=True,
        env=env,
    )


def test_bridge_refusal_restores_preexisting_destination_byte_identically(tmp_path):
    pack_dir, manifest, xaas_root = _make_fixture(tmp_path, BROKEN_BRIDGE)
    ontology = pack_dir / "ontology.ttl"
    bridge = xaas_root / "lib" / "xaas" / "sparql_bridge.ex"
    destination = xaas_root / OUTPUT_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(PREEXISTING_BYTES)
    ontology_before = ontology.read_bytes()
    bridge_before = bridge.read_bytes()

    result = _run(pack_dir, manifest, xaas_root)

    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "ROLLED BACK" in result.stderr
    assert ontology.read_bytes() == ontology_before
    assert destination.read_bytes() == PREEXISTING_BYTES
    assert bridge.read_bytes() == bridge_before


def test_bridge_refusal_removes_destination_created_by_failed_deploy(tmp_path):
    pack_dir, manifest, xaas_root = _make_fixture(tmp_path, BROKEN_BRIDGE)
    ontology = pack_dir / "ontology.ttl"
    destination = xaas_root / OUTPUT_REL
    ontology_before = ontology.read_bytes()
    assert not destination.exists()

    result = _run(pack_dir, manifest, xaas_root)

    assert result.returncode == 1, (result.stdout, result.stderr)
    assert ontology.read_bytes() == ontology_before
    assert not destination.exists(), "failed transaction left an orphaned XaaS module"


def test_success_commits_generated_resource_and_connector_state(tmp_path):
    pack_dir, manifest, xaas_root = _make_fixture(tmp_path, SUCCESS_BRIDGE)
    ontology = pack_dir / "ontology.ttl"
    bridge = xaas_root / "lib" / "xaas" / "sparql_bridge.ex"
    destination = xaas_root / OUTPUT_REL

    result = _run(pack_dir, manifest, xaas_root)

    assert result.returncode == 0, (result.stdout, result.stderr)
    assert destination.read_bytes() == GENERATED_BYTES
    assert f'aac:invokeTool "{TOOL_NAME}"' in ontology.read_text()
    bridge_text = bridge.read_text()
    assert "alias Xaas.Operations.AutofdePlannerTransactionTest" in bridge_text
    assert "transaction_test_to_turtle" in bridge_text
    assert "OK: transactional connector deploy committed filesystem state" in result.stdout
