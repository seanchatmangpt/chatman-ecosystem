#!/usr/bin/env python3
"""Verify one generated failure-immunity consumer against the canonical root-crown witness."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

SCHEMA = "https://chatman.dev/standing-court/inherited-negative-receipt/v2"

def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("canonical_root_crown_mutate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--canonical-root", type=Path, required=True)
    p.add_argument("--projection", type=Path, required=True)
    p.add_argument("--adversary", type=Path, required=True)
    p.add_argument("--consumer-repository", required=True)
    p.add_argument("--consumer-head", required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--check", type=Path)
    a = p.parse_args()

    projection = json.loads(a.projection.read_text(encoding="utf-8"))
    adversary = json.loads(a.adversary.read_text(encoding="utf-8"))
    if projection.get("consumer_subject") != a.consumer_repository:
        raise SystemExit("REFUSED[CONSUMER_SUBJECT_MISMATCH]")
    inherited = set(projection.get("inherited_guards", []))
    if "REPLAY_DIVERGED" not in inherited:
        raise SystemExit("REFUSED[INHERITED_GUARD_MISSING]")
    if adversary.get("failure_class") != "REPLAY_MISMATCH" or adversary.get("expected_guard") != "REPLAY_DIVERGED":
        raise SystemExit("REFUSED[ADVERSARY_MISMATCH]")

    canonical = a.canonical_root.resolve()
    mutate = load_module(canonical / "scripts/release_train/root_crown/mutate.py")
    witness = next(dm for dm in mutate.DATA_MUTANTS if dm.name == "dm_replay_mismatch")
    report = mutate.run(canonical, source=(), data=(witness,))
    result = report["mutants"]["dm_replay_mismatch"]
    killed = bool(result["killed"]) and "REPLAY_DIVERGED" in result["expected"]
    receipt = {
        "schema": SCHEMA,
        "receipt_kind": "OBSERVED_INHERITED_NEGATIVE_EXECUTION",
        "failure_class": "REPLAY_MISMATCH",
        "guard": "REPLAY_DIVERGED",
        "consumer": {
            "repository": a.consumer_repository,
            "head_sha": a.consumer_head,
            "projection_base_sha": projection.get("consumer_base_sha"),
        },
        "canonical": {
            "repository": "seanchatmangpt/chatman-ecosystem",
            "commit": projection.get("canonical_commit"),
            "source": projection.get("canonical_source"),
            "falsifier": "dm_replay_mismatch",
        },
        "observation": {
            "status": "ALIVE" if killed else "NONCONFORMANT",
            "canonical_witness_killed": killed,
            "detail": result["detail"],
            "credit_prevention": killed,
        },
        "metric": {
            "failures_originally_observed": 1,
            "failures_prevented_in_other_subjects": 1 if killed else 0,
        },
        "authority": "NONE",
    }
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if a.check:
        return 0 if a.check.read_text(encoding="utf-8") == rendered else 2
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if killed else 1

if __name__ == "__main__":
    raise SystemExit(main())
