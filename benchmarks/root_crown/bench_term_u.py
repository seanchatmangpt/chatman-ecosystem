"""Deterministic timing benchmark for the root crown's term-U composition (PR #295).

Stdlib only; real collaborators (the ``UTree`` v26.9.26-shaped release tree from
``tests/release_train/root_crown/test_term_u.py``, the real projector, the real crown and the
real autonomic_crown sealer). Four cases, each timed ``--iterations`` times after one warm-up:

- ``release_terms``: premise term-set derivation (pure function);
- ``validate_requirements``: premise-set admission of the U premise;
- ``autonomic_receipt``: the U evaluator on a sealed AUTONOMIC receipt (digest + binding);
- ``crown_evaluate``: the whole crown over the U tree (ALIVE positive control).

Every timed call's result is also checked (the crown must be ALIVE, U must PASS), so a
benchmark that got faster by breaking the court fails instead of reporting a speed-up.

``--write`` records ``benchmarks/root_crown/term-u-bench.json``; ``--check`` re-measures and
exits 1 when any case's median exceeds ``REGRESSION_FACTOR`` x its recorded median (floored
at ``FLOOR_S`` so sub-millisecond cases do not flap on scheduler noise). Exit 0 within bound.
Authority: NONE.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests/release_train/root_crown"
RECEIPT = REPO / "benchmarks/root_crown/term-u-bench.json"
SCHEMA = "https://chatman.dev/root-crown/bench/term-u/v1"
REGRESSION_FACTOR = 5.0
FLOOR_S = 0.005

for entry in (str(REPO), str(TESTS)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from scripts.release_train.root_crown import evidence, projector  # noqa: E402
from scripts.release_train.root_crown.model import release_terms  # noqa: E402
from scripts.release_train.root_crown.requirements import validate_requirements  # noqa: E402
from test_term_u import NEW, UTree  # noqa: E402


def _time(fn: Callable[[], Any], check: Callable[[Any], bool], iterations: int) -> dict[str, Any]:
    if not check(fn()):
        raise SystemExit("bench: warm-up result failed its correctness check")
    samples = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = fn()
        samples.append(time.perf_counter() - start)
        if not check(result):
            raise SystemExit("bench: timed result failed its correctness check")
    samples.sort()
    return {
        "iterations": iterations,
        "median_s": round(statistics.median(samples), 6),
        "p95_s": round(samples[min(len(samples) - 1, int(0.95 * len(samples)))], 6),
        "min_s": round(samples[0], 6),
    }


def measure(iterations: int) -> dict[str, Any]:
    tree = UTree()
    try:
        tree.write_receipt()
        inputs = projector.load_inputs(tree.release_dir)
        doc = inputs.requirements_doc
        req = next(r for r in inputs.requirements if r.id == "U-01")
        ctx = tree.ctx()
        cases = {
            "release_terms": _time(lambda: release_terms(doc, NEW), lambda r: r[1] == [] and "U" in r[0], iterations * 100),
            "validate_requirements": _time(
                lambda: validate_requirements(
                    doc, inputs.pins, inputs.rfc_text, evidence.EVALUATORS, inputs.premise_set, release=NEW
                ),
                lambda r: r == [],
                iterations,
            ),
            "autonomic_receipt": _time(
                lambda: evidence.autonomic_receipt(req, ctx), lambda s: s.state == "PASS", iterations
            ),
            "crown_evaluate": _time(tree.evaluate, lambda v: v.standing == "ALIVE", max(3, iterations // 5)),
        }
    finally:
        tree.cleanup()
    return {
        "schema": SCHEMA,
        "subject": "tests/release_train/root_crown/test_term_u.py::UTree (v26.9.26-shaped, ALIVE)",
        "python": platform.python_version(),
        "machine": platform.machine(),
        "regression_factor": REGRESSION_FACTOR,
        "floor_s": FLOOR_S,
        "cases": cases,
        "authority": "NONE",
    }


def regressions(recorded: dict[str, Any], current: dict[str, Any]) -> list[str]:
    out = []
    for name, rec in recorded["cases"].items():
        cur = current["cases"].get(name)
        if cur is None:
            out.append(f"{name}: case missing")
            continue
        bound = max(rec["median_s"] * recorded["regression_factor"], recorded["floor_s"])
        if cur["median_s"] > bound:
            out.append(f"{name}: median {cur['median_s']}s > bound {bound:.6f}s (recorded {rec['median_s']}s)")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 benchmarks/root_crown/bench_term_u.py")
    parser.add_argument("--iterations", type=int, default=20)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help=f"record {RECEIPT.relative_to(REPO)}")
    mode.add_argument("--check", action="store_true", help="re-measure; exit 1 on a regression past the bound")
    args = parser.parse_args(argv)
    current = measure(args.iterations)
    print(json.dumps(current, indent=2, sort_keys=True))
    if args.write:
        RECEIPT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    if args.check:
        found = regressions(json.loads(RECEIPT.read_text(encoding="utf-8")), current)
        for line in found:
            print(f"REGRESSION {line}", file=sys.stderr)
        return 1 if found else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
