from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HEAD = "18294174c2d1262821975c08f2843f4a6c29a80c"
TREE = "e31e5d50028b0e2a26ac6a6b4dd466319315e22a"


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    receipt_dir = Path(sys.argv[2]).resolve()
    receipt_dir.mkdir(parents=True, exist_ok=True)

    compile_result = run([sys.executable, "-m", "compileall", "-q", "src", "tests"], cwd=root)
    (receipt_dir / "compile.stdout.log").write_text(compile_result.stdout)
    (receipt_dir / "compile.stderr.log").write_text(compile_result.stderr)

    tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root)
    (receipt_dir / "unit.stdout.log").write_text(tests.stdout)
    (receipt_dir / "unit.stderr.log").write_text(tests.stderr)
    unit_text = tests.stdout + "\n" + tests.stderr
    assert "Ran 9 tests" in unit_text and "OK" in unit_text, unit_text

    catalog_process = run(
        [
            "mfw-pypi-planner",
            "catalog",
            "--register",
            "tamerlite=tamerlite.engine:TamerLite",
            "--load-module",
            "up_paraspace",
            "--register",
            "spiderplan=up_spiderplan.solver:EngineImpl",
        ]
    )
    (receipt_dir / "catalog.stderr.log").write_text(catalog_process.stderr)
    catalog = json.loads(catalog_process.stdout)
    (receipt_dir / "catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")

    expected_distributions = {
        "unified-planning",
        "up-pyperplan",
        "up-tamer",
        "up-enhsp",
        "up-fast-downward",
        "up-lpg",
        "up-fmap",
        "up-aries",
        "up-symk",
        "tamerlite",
        "up-paraspace",
        "up-spiderplan",
    }
    missing = sorted(name for name in expected_distributions if catalog["distributions"].get(name) is None)
    assert not missing, {"missing_distributions": missing, "catalog": catalog}
    engine_names = {engine["name"] for engine in catalog["engines"]}
    for name in ("pyperplan", "tamerlite", "paraspace", "spiderplan"):
        assert name in engine_names, {"missing_engine": name, "engines": sorted(engine_names)}

    run_dir = receipt_dir / "pyperplan"
    run_dir.mkdir()
    domain = root / "tests" / "fixtures" / "domain.pddl"
    problem = root / "tests" / "fixtures" / "problem.pddl"
    candidate = run_dir / "candidate.plan"
    solve = run(
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
            "pyperplan",
            "--mode",
            "classical",
            "--timeout",
            "30",
        ]
    )
    (run_dir / "solve.stdout.json").write_text(solve.stdout)
    (run_dir / "solve.stderr.log").write_text(solve.stderr)
    stdout_receipt = json.loads(solve.stdout)
    sidecar_path = Path(str(candidate) + ".json")
    sidecar_receipt = json.loads(sidecar_path.read_text())
    assert stdout_receipt["status"] == "found", stdout_receipt
    assert sidecar_receipt["status"] == "found", sidecar_receipt
    for field in ("engine", "planner_status", "native_plan_kind", "emitted_plan_kind", "step_count"):
        assert stdout_receipt[field] == sidecar_receipt[field], (field, stdout_receipt, sidecar_receipt)
    assert candidate.read_text().strip() == "(finish)", candidate.read_text()

    wheel_dir = receipt_dir / "wheelhouse"
    wheel_dir.mkdir()
    run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(wheel_dir), str(root)])
    wheels = sorted(wheel_dir.glob("mfw_pypi_planner-*.whl"))
    assert len(wheels) == 1, wheels

    receipt = {
        "schema": "urn:chatman:mfw-python-federation-crown:v1",
        "status": "ALIVE",
        "mfw_head_sha": HEAD,
        "mfw_tree_sha": TREE,
        "unit_tests": 9,
        "cli_stdout_receipt": "clean_json",
        "candidate": candidate.read_text().strip(),
        "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "sidecar_sha256": hashlib.sha256(sidecar_path.read_bytes()).hexdigest(),
        "wheel": wheels[0].name,
        "wheel_sha256": hashlib.sha256(wheels[0].read_bytes()).hexdigest(),
        "distributions": catalog["distributions"],
        "engine_names": sorted(engine_names),
        "plugin_admission": catalog["plugin_admission"],
    }
    (receipt_dir / "receipt-python-federation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
