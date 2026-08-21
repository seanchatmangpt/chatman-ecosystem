#!/usr/bin/env python3
"""Chicago-style filesystem tests for provenance-fenced connector deployment."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "deploy_connector_with_provenance.py"
TOOL = "fabric__cache-stats"
REL = Path("lib/xaas/operations/autofde_planner_cache_stats.ex")


def receipt_for(root: Path, content: bytes) -> dict[str, str]:
    return {
        "schema": "chatman.ash-connector-provenance/1",
        "tool_name": TOOL,
        "output_file": str(REL),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def run_case(root: Path, new_bytes: str = "generated-v2\n", marker: Path | None = None):
    pack = root / "pack"
    xaas = root / "xaas"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "ontology.ttl").write_text("ontology-before\n")
    bridge = xaas / "lib/xaas/sparql_bridge.ex"
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_text("bridge-before\n")
    dest = xaas / REL
    code = (
        "from pathlib import Path; import os; "
        "p=Path(os.environ['TEST_DEST']); p.parent.mkdir(parents=True, exist_ok=True); "
        "p.write_text(os.environ['TEST_NEW_BYTES']); "
        + ("Path(os.environ['TEST_MARKER']).write_text('ran')" if marker else "")
    )
    env = os.environ.copy()
    env.update(
        {
            "CONNECTOR_PACK_DIR": str(pack),
            "XAAS_ROOT": str(xaas),
            "TEST_DEST": str(dest),
            "TEST_NEW_BYTES": new_bytes,
            "CONNECTOR_TRANSACTION_CMD_OVERRIDE": json.dumps([sys.executable, "-c", code]),
        }
    )
    if marker:
        env["TEST_MARKER"] = str(marker)
    result = subprocess.run([sys.executable, str(SCRIPT), TOOL], env=env, text=True, capture_output=True)
    return result, dest, Path(str(dest) + ".ggen-provenance.json")


def test_first_write_creates_destination_and_receipt():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result, dest, sidecar = run_case(root)
        assert result.returncode == 0, result.stderr
        content = dest.read_bytes()
        assert content == b"generated-v2\n"
        assert json.loads(sidecar.read_text()) == receipt_for(root / "xaas", content)


def test_generator_owned_destination_can_be_replaced_and_receipt_advances():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        xaas = root / "xaas"
        dest = xaas / REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        old = b"generated-v1\n"
        dest.write_bytes(old)
        sidecar = Path(str(dest) + ".ggen-provenance.json")
        sidecar.write_text(json.dumps(receipt_for(xaas, old), sort_keys=True, separators=(",", ":")) + "\n")
        result, dest, sidecar = run_case(root)
        assert result.returncode == 0, result.stderr
        assert dest.read_bytes() == b"generated-v2\n"
        assert json.loads(sidecar.read_text()) == receipt_for(xaas, b"generated-v2\n")


def test_hand_edited_destination_refuses_without_running_child():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        xaas = root / "xaas"
        dest = xaas / REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        generated = b"generated-v1\n"
        dest.write_bytes(generated)
        sidecar = Path(str(dest) + ".ggen-provenance.json")
        sidecar.write_text(json.dumps(receipt_for(xaas, generated)))
        dest.write_bytes(b"human edit\n")
        marker = root / "child-ran"
        result, _, _ = run_case(root, marker=marker)
        assert result.returncode == 1
        assert "provenance mismatch" in result.stderr
        assert dest.read_bytes() == b"human edit\n"
        assert not marker.exists()


def test_existing_destination_without_receipt_refuses():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "xaas" / REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("legacy bytes\n")
        marker = root / "child-ran"
        result, _, _ = run_case(root, marker=marker)
        assert result.returncode == 1
        assert "no generator provenance receipt" in result.stderr
        assert dest.read_text() == "legacy bytes\n"
        assert not marker.exists()


def test_malformed_receipt_refuses():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "xaas" / REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("generated-v1\n")
        Path(str(dest) + ".ggen-provenance.json").write_text("not-json")
        marker = root / "child-ran"
        result, _, _ = run_case(root, marker=marker)
        assert result.returncode == 1
        assert "invalid provenance receipt" in result.stderr
        assert not marker.exists()


def test_orphan_receipt_without_destination_refuses():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dest = root / "xaas" / REL
        dest.parent.mkdir(parents=True, exist_ok=True)
        Path(str(dest) + ".ggen-provenance.json").write_text("{}")
        marker = root / "child-ran"
        result, _, _ = run_case(root, marker=marker)
        assert result.returncode == 1
        assert "orphan provenance sidecar" in result.stderr
        assert not marker.exists()
