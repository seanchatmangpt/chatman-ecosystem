#!/usr/bin/env python3
"""Longitudinal BFCC-E/BFCC-T benchmark over a JSONL ledger of verified receipts.

Aggregates pre-existing, independently-verified receipts -- it does not itself
compute or measure capability. OBSERVE only: no DO action, no mutation of any
receipt it reads. Pure Python stdlib, no numpy/scipy: least-squares slope is
computed by hand.

For each problem_class with >=2 receipts, this fits a least-squares linear trend
of eta (verified_capability_delta / sum(resource_vector.values())) against receipt
order, and classifies the direction as exactly one of IMPROVING / DEGRADING / FLAT /
INSUFFICIENT_DATA -- never a silent fifth state, never omitted. The same computation
is performed for lambda (trimtab leverage) using canonical_information_delta when
present in a receipt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPTS = ROOT / ".artifacts" / "bfcc" / "receipts.jsonl"

DEFAULT_EPSILON = 1e-6

DIRECTIONS = ("IMPROVING", "DEGRADING", "FLAT", "INSUFFICIENT_DATA")


def load_receipts(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL ledger of receipts. Missing/empty/non-JSONL files yield []."""
    if not path.exists() or not path.is_file():
        return []
    receipts: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        row = json.loads(stripped)
        if isinstance(row, dict):
            receipts.append(row)
    return receipts


def least_squares_slope(ys: list[float]) -> float:
    """Fit y = a + b*x by hand (x = 0..n-1, ordinary least squares), return b.

    Caller must ensure len(ys) >= 2.
    """
    n = len(ys)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def classify_direction(values: list[float], epsilon: float) -> tuple[str, float | None]:
    """Return (direction, slope) for a series of per-receipt metric values."""
    if len(values) < 2:
        return "INSUFFICIENT_DATA", None
    slope = least_squares_slope(values)
    if abs(slope) < epsilon:
        return "FLAT", slope
    if slope > 0:
        return "IMPROVING", slope
    return "DEGRADING", slope


def compute_eta(receipt: dict[str, Any]) -> float | None:
    resource_vector = receipt.get("resource_vector")
    verified_capability_delta = receipt.get("verified_capability_delta")
    if not isinstance(resource_vector, dict) or not resource_vector:
        return None
    if verified_capability_delta is None:
        return None
    total_resource = sum(
        value for value in resource_vector.values() if isinstance(value, (int, float))
    )
    if total_resource == 0:
        return None
    return verified_capability_delta / total_resource


def compute_lambda(receipt: dict[str, Any]) -> float | None:
    resource_vector = receipt.get("resource_vector")
    canonical_information_delta = receipt.get("canonical_information_delta")
    if not isinstance(resource_vector, dict) or not resource_vector:
        return None
    if canonical_information_delta is None:
        return None
    total_resource = sum(
        value for value in resource_vector.values() if isinstance(value, (int, float))
    )
    if total_resource == 0:
        return None
    return canonical_information_delta / total_resource


def benchmark(receipts: list[dict[str, Any]], epsilon: float = DEFAULT_EPSILON) -> dict[str, Any]:
    problem_classes: dict[str, list[dict[str, Any]]] = {}
    for receipt in receipts:
        problem_class = receipt.get("problem_class")
        if not isinstance(problem_class, str) or not problem_class:
            continue
        problem_classes.setdefault(problem_class, []).append(receipt)

    report: dict[str, Any] = {}
    for problem_class, class_receipts in problem_classes.items():
        eta_values = [
            eta for eta in (compute_eta(receipt) for receipt in class_receipts) if eta is not None
        ]
        lambda_values = [
            lam
            for lam in (compute_lambda(receipt) for receipt in class_receipts)
            if lam is not None
        ]

        eta_direction, eta_slope = classify_direction(eta_values, epsilon)
        lambda_direction, lambda_slope = classify_direction(lambda_values, epsilon)

        report[problem_class] = {
            "receipt_count": len(class_receipts),
            "eta": {
                "n": len(eta_values),
                "direction": eta_direction,
                "slope": eta_slope,
                "values": eta_values,
            },
            "lambda": {
                "n": len(lambda_values),
                "direction": lambda_direction,
                "slope": lambda_slope,
                "values": lambda_values,
            },
        }

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts", type=Path, default=DEFAULT_RECEIPTS)
    parser.add_argument("--epsilon", type=float, default=DEFAULT_EPSILON)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    receipts = load_receipts(args.receipts)
    report = benchmark(receipts, epsilon=args.epsilon)

    if args.json:
        print(json.dumps({"problem_classes": report}))
    else:
        if not report:
            print("INSUFFICIENT_DATA: no problem_class found in ledger")
        for problem_class, entry in report.items():
            print(
                f"{problem_class}: eta={entry['eta']['direction']} "
                f"lambda={entry['lambda']['direction']}"
            )

    any_degrading = any(
        entry["eta"]["direction"] == "DEGRADING" or entry["lambda"]["direction"] == "DEGRADING"
        for entry in report.values()
    )
    if any_degrading:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
