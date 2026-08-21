#!/usr/bin/env python3
"""Chicago-style court for preflight-to-deploy exact-state binding."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "deploy_connector_with_provenance.py"
TOOL = "fabric__cache-stats"
REL = Path("lib/xaas/operations/autofde_planner_cache_stats.ex")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
    child = (
        "from pathlib import Path; "
        f"Path({str(marker)!r}).write_text('ran'); "
        f"p=Path({str(dest)!r}); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'generated-v2\\n')"
    )
    env = os.environ.copy()
    env.update(
        {
            "CONNECTOR_PACK_DIR": str(pack),
            "XAAS_ROOT": str(xaas),
            "CONNECTOR_TRANSACTION_CMD_OVERRIDE": json.dumps([sys.executable, "-c", child]),
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


def run_bound_deploy(env: dict[str, str], digest: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--admission-digest", digest, TOOL],
        env=env,
        text=True,
        capture_output=True,
    )


def snapshot(*paths: Path) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def test_preflight_digest_is_deterministic_and_root_path_independent():
    records = []
    for _ in range(2):
        with tempfile.TemporaryDirectory() as td:
            env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
            first = run_check(env)
            second = run_check(env)
            assert first.returncode == second.returncode == 0
            first_record = json.loads(first.stdout)
            second_record = json.loads(second.stdout)
            assert first_record == second_record
            assert SHA256_RE.fullmatch(first_record["admission_digest"])
            assert not marker.exists()
            records.append(first_record)
    assert records[0]["admission_digest"] == records[1]["admission_digest"]


def test_exact_digest_allows_existing_deploy_and_commits_receipt():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        check = run_check(env)
        assert check.returncode == 0, check.stderr
        digest = json.loads(check.stdout)["admission_digest"]

        deploy = run_bound_deploy(env, digest)
        assert deploy.returncode == 0, deploy.stderr
        assert marker.read_text() == "ran"
        assert dest.read_bytes() == b"generated-v2\n"
        receipt = json.loads(sidecar.read_text())
        assert receipt["schema"] == "chatman.ash-connector-provenance/1"
        assert receipt["tool_name"] == TOOL
        assert receipt["output_file"] == str(REL)
        assert SHA256_RE.fullmatch(receipt["sha256"])


@pytest.mark.parametrize("surface", ["destination", "provenance", "ontology", "sparql_bridge"])
def test_stale_digest_refuses_before_child_and_preserves_current_state(surface: str):
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        check = run_check(env)
        assert check.returncode == 0, check.stderr
        digest = json.loads(check.stdout)["admission_digest"]

        if surface == "destination":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"concurrent-destination\n")
        elif surface == "provenance":
            dest.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_bytes(b"concurrent-sidecar\n")
        elif surface == "ontology":
            ontology.write_bytes(b"concurrent-ontology\n")
        elif surface == "sparql_bridge":
            bridge.write_bytes(b"concurrent-bridge\n")
        before = snapshot(ontology, bridge, dest, sidecar, marker)

        deploy = run_bound_deploy(env, digest)
        assert deploy.returncode == 1
        assert "REFUSED: stale admission digest" in deploy.stderr
        assert snapshot(*before) == before
        assert marker.exists() is False


def test_malformed_digest_refuses_before_child_without_mutation():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        before = snapshot(ontology, bridge, dest, sidecar, marker)
        deploy = run_bound_deploy(env, "not-a-sha256")
        assert deploy.returncode == 1
        assert "admission digest must be exactly 64 lowercase hexadecimal characters" in deploy.stderr
        assert snapshot(*before) == before
        assert marker.exists() is False


def test_legacy_direct_deploy_without_digest_remains_supported():
    with tempfile.TemporaryDirectory() as td:
        env, ontology, bridge, dest, sidecar, marker = fixture(Path(td))
        deploy = subprocess.run(
            [sys.executable, str(SCRIPT), TOOL],
            env=env,
            text=True,
            capture_output=True,
        )
        assert deploy.returncode == 0, deploy.stderr
        assert marker.read_text() == "ran"
        assert dest.read_bytes() == b"generated-v2\n"
        assert sidecar.exists()
