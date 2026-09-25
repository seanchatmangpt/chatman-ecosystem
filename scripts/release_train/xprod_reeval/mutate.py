"""Case-level mutants generated from the committed case (never stored).

Each mutant is derived in memory from the committed case JSON, written to
a temporary directory next to copies of nothing (evidence paths are rebased
to the committed case directory), and must come out non-ALIVE with the
expected typed line:

  sha_drift          one evidence subject_sha changed
                     -> REFUSED:SUBJECT_IDENTITY_SPLIT
  missing_producer   all BRCE evidence dropped
                     -> BLOCKED:MISSING_DIMENSION:BRCE
  authority_do       one evidence authority set to "DO"
                     -> REFUSED:INADMISSIBLE_CASE (court exit 2)
  digest_mismatch    one artifact_digest changed
                     -> REFUSED:ARTIFACT_DIGEST_MISMATCH:<eid> (provenance)

Exit 0 iff every mutant is killed with its expected line.
"""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from scripts.release_train.cross_product_court.__main__ import run as court_run

from .provenance import verify_offline


def _flip_hex(value: str) -> str:
    last = value[-1]
    return value[:-1] + ("0" if last != "0" else "1")


def _first(raw: dict[str, Any], formalism: str) -> dict[str, Any]:
    for item in raw["evidence"]:
        if item["formalism"] == formalism:
            return item
    raise LookupError(f"no {formalism} evidence in case")


def mutate_sha_drift(raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
    item = _first(raw, "OCEL2")
    item["subject_sha"] = _flip_hex(item["subject_sha"])
    return raw, "REFUSED:SUBJECT_IDENTITY_SPLIT:" + item["repository"]


def mutate_missing_producer(
    raw: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    raw["evidence"] = [x for x in raw["evidence"] if x["formalism"] != "BRCE"]
    return raw, "BLOCKED:MISSING_DIMENSION:BRCE"


def mutate_authority_do(raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
    _first(raw, "RECEIPT")["authority"] = "DO"
    return raw, "REFUSED:INADMISSIBLE_CASE:"


def mutate_digest_mismatch(
    raw: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    item = _first(raw, "POWL")
    item["artifact_digest"] = _flip_hex(item["artifact_digest"])
    return raw, "REFUSED:ARTIFACT_DIGEST_MISMATCH:" + item["evidence_id"]


MUTANTS: dict[str, tuple[Callable, str]] = {
    "sha_drift": (mutate_sha_drift, "court"),
    "missing_producer": (mutate_missing_producer, "court"),
    "authority_do": (mutate_authority_do, "court"),
    "digest_mismatch": (mutate_digest_mismatch, "provenance"),
}


def _rebase(raw: dict[str, Any], base: Path) -> None:
    for item in raw["evidence"]:
        prov = item.get("provenance")
        if isinstance(prov, dict):
            for key in ("file", "validator_file"):
                if key in prov:
                    prov[key] = str((base / prov[key]).resolve())


def run_mutants(case_path: str | Path) -> dict[str, Any]:
    case_path = Path(case_path)
    original = json.loads(case_path.read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="xprod-mutant-") as td:
        for name, (mutator, court) in MUTANTS.items():
            raw = copy.deepcopy(original)
            _rebase(raw, case_path.parent)
            raw, expected = mutator(raw)
            path = Path(td) / f"{name}.json"
            path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            if court == "court":
                report, code = court_run(str(path))
            else:
                report = verify_offline(path)
                code = 2 if report["standing"] == "REFUSED" else 0
            lines = report.get("refusals", [])
            killed = (
                report.get("standing") != "ALIVE"
                and code != 0
                and any(line.startswith(expected) for line in lines)
            )
            results[name] = {
                "expected": expected,
                "observed_standing": report.get("standing"),
                "exit_code": code,
                "refusals": lines,
                "killed": killed,
            }
    return {
        "case_id": original.get("case_id"),
        "mutants": results,
        "all_killed": all(r["killed"] for r in results.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case")
    args = parser.parse_args(argv)
    report = run_mutants(args.case)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_killed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
