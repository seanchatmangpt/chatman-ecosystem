#!/usr/bin/env python3
"""Chicago-style court for SELECT-only connector provenance preflight."""
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


def receipt_for(content: bytes) -> dict[str, str]:
    return {
        "schema": "chatman.ash-connector-provenance/1",
        "tool_name": TOOL,
        "output_file": str(REL),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def fixture(root: Path):
    pack = root / "pack"
    xaas = root / "xaas"
    pack.mkdir(parents=True)
    ontology = pack / "ontology.ttl"
    ontology.write_bytes(b"ontology-before\n")
    bridge = xaas / "lib/xaas/sparql_bridge.ex"
    bridge.parent.mkdir(parents=True, exist_ok=True)
    bridge.write_bytes(b"bridge-before\n")
    dest = xaas / REL
    sidecar = Path(str(dest) + ".ggen-provenance.json")
    marker = root / "child-ran"
    env = os.environ.copy()
    env.update(
        {
            "CONNECTOR_PACK_DIR": str(pack),
            "XAAS_ROOT": str(xaas),
            "CONNECTOR_TRANSACTION_CMD_OVERRIDE": json.dumps(
                [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"]
            ),
        }
    )
    return env, ontology, bridge, dest, sidecar, marker


def run_check(env: dict[str, str]):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--check", TOOL],
        env=env,
        text=True,
        capture_output=True,
    )


def snapshot(*paths: Path) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def assert_unchanged(before: dict[Path, bytes | None]) -> None:
    after = snapshot(*before)
    assert after == before


def test_check_admits_first_write_without_mutation_or_child():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 0, result.stderr
        record = json.loads(result.stdout)
        assert record == {
            "schema": "chatman.ash-connector-preflight/1",
            "tool_name": TOOL,
            "output_file": str(REL),
            "admitted": True,
            "disposition": "first_write",
            "reason": "destination absent and no orphan provenance sidecar exists",
            "authority": "SELECT_ONLY",
            "child_invoked": False,
        }
        assert_unchanged(before)


def test_check_admits_exact_generator_owned_regeneration_without_mutation_or_child():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        generated = b"generated-v1\n"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(generated)
        sidecar.write_text(json.dumps(receipt_for(generated), sort_keys=True, separators=(",", ":")) + "\n")
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 0, result.stderr
        record = json.loads(result.stdout)
        assert record["admitted"] is True
        assert record["disposition"] == "regenerate"
        assert record["authority"] == "SELECT_ONLY"
        assert record["child_invoked"] is False
        assert_unchanged(before)


def test_check_refuses_hand_edit_with_machine_record_and_same_refusal_semantics():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        generated = b"generated-v1\n"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(generated)
        sidecar.write_text(json.dumps(receipt_for(generated)))
        dest.write_bytes(b"human edit\n")
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 1
        record = json.loads(result.stdout)
        assert record["admitted"] is False
        assert record["disposition"] == "refused"
        assert "provenance mismatch" in record["reason"]
        assert "REFUSED: provenance mismatch" in result.stderr
        assert_unchanged(before)


def test_check_refuses_missing_receipt_without_child():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"legacy bytes\n")
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 1
        assert "no generator provenance receipt" in result.stderr
        assert json.loads(result.stdout)["admitted"] is False
        assert_unchanged(before)


def test_check_refuses_malformed_receipt_without_child():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"generated-v1\n")
        sidecar.write_text("not-json")
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 1
        assert "invalid provenance receipt" in result.stderr
        assert json.loads(result.stdout)["admitted"] is False
        assert_unchanged(before)


def test_check_refuses_orphan_receipt_without_child():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        dest.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text("{}")
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        result = run_check(env)
        assert result.returncode == 1
        assert "orphan provenance sidecar" in result.stderr
        assert json.loads(result.stdout)["admitted"] is False
        assert_unchanged(before)
