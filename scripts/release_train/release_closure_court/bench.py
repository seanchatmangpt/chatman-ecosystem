"""Deterministic timing benchmark for the release closure court lineage/dependency laws.

``python3 -m scripts.release_train.release_closure_court.bench [--sizes 100,500,2000] [--reps 5]``
prints a JSON receipt: for each size ``n`` a synthetic closure of ``n`` subjects (every
subject a typed ``BLOCKED`` row carrying a 3-PR lineage and a dependency on its successor,
i.e. a length-``n`` chain, the worst case for recursion depth and repair ordering) is
evaluated ``reps`` times; the median wall time in milliseconds is recorded together with
the receipt digest, which must be identical across reps (replay). Pure computation: no
network, no subprocess, no filesystem writes.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from typing import Any

from .court import evaluate, repair_order

SCHEMA = "https://chatman.dev/release-closure-court/bench/v1"


def _sha(i: int, salt: int) -> str:
    return f"{(i * 7919 + salt) & 0xFFFFFFFF:08x}" * 5


def synthetic_closure(n: int) -> dict[str, Any]:
    """Length-``n`` dependency chain; each row: 1 CANONICAL (MERGED) + 2 CLOSED lineage PRs."""
    subjects = []
    for i in range(n):
        sha = _sha(i, 1)
        subjects.append(
            {
                "subject_id": f"S{i:06d}",
                "repository": f"o/r{i % 17}",
                "artifact": f"lib/s{i}.ex",
                "sha": sha,
                "required": True,
                "spec_standing": "NOT_A_SPEC",
                "impl_standing": "BLOCKED",
                "impl_type": "bench:synthetic",
                "courts": [],
                "lineage": [
                    {"pr": 3 * i + 3, "sha": sha, "state": "MERGED", "draft": False,
                     "mergeable": "UNKNOWN", "disposition": "CANONICAL", "additions": i % 997},
                    {"pr": 3 * i + 1, "sha": _sha(i, 2), "state": "CLOSED_UNMERGED", "draft": False,
                     "mergeable": "UNKNOWN", "disposition": "SUPERSEDED", "additions": 5},
                    {"pr": 3 * i + 2, "sha": _sha(i, 3), "state": "CLOSED_UNMERGED", "draft": False,
                     "mergeable": "UNKNOWN", "disposition": "CLOSED", "additions": 5},
                ],
                "depends_on": [f"S{i + 1:06d}"] if i + 1 < n else [],
            }
        )
    return {
        "release": "bench",
        "normative_ledger": "bench",
        "max_canonical_additions": 1000,
        "subjects": subjects,
    }


def run(sizes: list[int], reps: int) -> dict[str, Any]:
    results = []
    for n in sizes:
        closure = synthetic_closure(n)
        times, digests = [], set()
        for _ in range(reps):
            t0 = time.perf_counter()
            verdict = evaluate(closure)
            times.append((time.perf_counter() - t0) * 1000.0)
            digests.add(verdict.receipt["receipt_digest"])
        ids = {r["subject_id"] for r in closure["subjects"]}
        t0 = time.perf_counter()
        order = repair_order(closure["subjects"], ids)
        order_ms = (time.perf_counter() - t0) * 1000.0
        results.append(
            {
                "n": n,
                "standing": verdict.standing,
                "refusals": len(verdict.refusals),
                "evaluate_median_ms": round(statistics.median(times), 3),
                "evaluate_max_ms": round(max(times), 3),
                "repair_order_ms": round(order_ms, 3),
                "repair_order_first": order[0],
                "repair_order_last": order[-1],
                "replay_identical": len(digests) == 1,
            }
        )
    return {"schema": SCHEMA, "reps": reps, "python": sys.version.split()[0], "results": results,
            "authority": "NONE"}


def main(argv: list[str]) -> int:
    sizes, reps = [100, 500, 2000], 5
    args = argv[1:]
    if "--sizes" in args:
        sizes = [int(x) for x in args[args.index("--sizes") + 1].split(",")]
    if "--reps" in args:
        reps = int(args[args.index("--reps") + 1])
    print(json.dumps(run(sizes, reps), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
