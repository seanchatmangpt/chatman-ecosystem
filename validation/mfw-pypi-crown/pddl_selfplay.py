from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

HEAD = "18294174c2d1262821975c08f2843f4a6c29a80c"
TREE = "e31e5d50028b0e2a26ac6a6b4dd466319315e22a"
VAL_COMMIT = "3c7a1f330bdab0ba28a4762bb45c3f06c27fb6d4"
ENGINES = (
    "pyperplan",
    "fast-downward",
    "enhsp",
    "lpg",
    "tamer",
    "symk",
    "aries",
)


def main() -> None:
    capsule = Path(sys.argv[1]).resolve()
    validator = Path(sys.argv[2]).resolve()
    receipt_root = Path(sys.argv[3]).resolve()
    receipt_root.mkdir(parents=True, exist_ok=True)
    domain = capsule / "tests" / "fixtures" / "domain.pddl"
    problem = capsule / "tests" / "fixtures" / "problem.pddl"

    receipts: list[dict[str, object]] = []
    for engine in ENGINES:
        run_dir = receipt_root / engine
        run_dir.mkdir()
        candidate = run_dir / "candidate.plan"
        sidecar = Path(str(candidate) + ".json")
        started = time.perf_counter_ns()
        solve = subprocess.run(
            [
                "mfw-pypi-planner",
                "solve",
                "--domain",
                str(domain),
                "--problem",
                str(problem),
                "--plan",
                str(candidate),
                "--engine",
                engine,
                "--mode",
                "classical",
                "--timeout",
                "60",
            ],
            text=True,
            capture_output=True,
            timeout=180,
        )
        solve_ms = (time.perf_counter_ns() - started) / 1_000_000
        (run_dir / "solve.stdout.json").write_text(solve.stdout)
        (run_dir / "solve.stderr.log").write_text(solve.stderr)
        assert solve.returncode == 0, {
            "engine": engine,
            "returncode": solve.returncode,
            "stdout": solve.stdout,
            "stderr": solve.stderr,
        }
        stdout_receipt = json.loads(solve.stdout)
        assert sidecar.is_file(), {"engine": engine, "missing_sidecar": str(sidecar)}
        sidecar_receipt = json.loads(sidecar.read_text())
        assert stdout_receipt["status"] == "found", stdout_receipt
        assert sidecar_receipt["status"] == "found", sidecar_receipt
        for field in (
            "engine",
            "planner_status",
            "native_plan_kind",
            "emitted_plan_kind",
            "step_count",
        ):
            assert stdout_receipt[field] == sidecar_receipt[field], (
                engine,
                field,
                stdout_receipt,
                sidecar_receipt,
            )
        assert candidate.is_file() and candidate.stat().st_size > 0

        validation = subprocess.run(
            [
                str(validator),
                "-v",
                "-t",
                "0.001",
                str(domain),
                str(problem),
                str(candidate),
            ],
            text=True,
            capture_output=True,
            timeout=60,
        )
        (run_dir / "validator.stdout.log").write_text(validation.stdout)
        (run_dir / "validator.stderr.log").write_text(validation.stderr)
        validation_text = (validation.stdout + "\n" + validation.stderr).lower()
        assert validation.returncode == 0, {
            "engine": engine,
            "returncode": validation.returncode,
            "stdout": validation.stdout,
            "stderr": validation.stderr,
        }
        assert "plan valid" in validation_text, {
            "engine": engine,
            "validator_output": validation_text,
        }

        receipt = {
            "schema": "urn:chatman:mfw-real-pddl-engine:v2",
            "status": "ALIVE",
            "mfw_head_sha": HEAD,
            "mfw_tree_sha": TREE,
            "engine": engine,
            "planner_status": sidecar_receipt["planner_status"],
            "solve_ms": solve_ms,
            "step_count": sidecar_receipt["step_count"],
            "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
            "stdout_receipt_sha256": hashlib.sha256(solve.stdout.encode()).hexdigest(),
            "sidecar_sha256": hashlib.sha256(sidecar.read_bytes()).hexdigest(),
            "validator": f"KCL-Planning/VAL@{VAL_COMMIT}",
            "validation_status": "valid",
        }
        (run_dir / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        )
        receipts.append(receipt)

    aggregate = {
        "schema": "urn:chatman:mfw-real-pddl-engine-aggregate:v2",
        "status": "ALIVE",
        "mfw_head_sha": HEAD,
        "mfw_tree_sha": TREE,
        "requested_engines": list(ENGINES),
        "executed_engines": [receipt["engine"] for receipt in receipts],
        "independent_validator": f"KCL-Planning/VAL@{VAL_COMMIT}",
        "receipts": receipts,
    }
    (receipt_root / "receipt-pddl-selfplay.json").write_text(
        json.dumps(aggregate, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(aggregate, sort_keys=True))


if __name__ == "__main__":
    main()
