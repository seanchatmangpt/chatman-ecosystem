#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "catalog" / "tpcs.toml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class Refusal(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkItem:
    subject: str
    acceptance: str
    authority: str
    reversible: bool = True
    acceptance_mutated: bool = False
    actuation_receipted: bool = True
    replay_match: bool = True


def load_config(path: Path = CONFIG) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def validate_config(cfg: dict) -> None:
    stages = cfg.get("stage", [])
    ids = [stage["id"] for stage in stages]
    required = ["observe", "admit", "construct", "verify", "receipt", "replay", "standing"]
    if ids != required:
        raise ValueError(f"invalid stage order: {ids}")
    if cfg.get("mode") != "pull":
        raise ValueError("TPS requires pull flow")
    if not cfg.get("zero_unreceipted_actuation"):
        raise ValueError("zero unreceipted actuation must be preserved")
    if cfg.get("acceptance_mutation_authority"):
        raise ValueError("pipeline must not own acceptance mutation authority")
    for stage in stages:
        if not isinstance(stage.get("wip_limit"), int) or stage["wip_limit"] < 1:
            raise ValueError(f"invalid WIP limit for {stage['id']}")


def admit(item: WorkItem, cfg: dict) -> None:
    refusals = cfg["refusals"]
    if not SHA40.fullmatch(item.subject):
        raise Refusal(refusals["invalid_subject"])
    if not item.acceptance.strip():
        raise Refusal("REFUSED_MISSING_ACCEPTANCE")
    if item.authority not in {"SELECT", "CONSTRUCT", "DO"}:
        raise Refusal("REFUSED_INVALID_AUTHORITY")
    if not item.reversible:
        raise Refusal("REFUSED_IRREVERSIBLE_PLAN")
    if item.acceptance_mutated:
        raise Refusal(refusals["acceptance_mutation"])
    if item.authority == "DO" and not item.actuation_receipted:
        raise Refusal(refusals["unreceipted_actuation"])
    if not item.replay_match:
        raise Refusal(refusals["replay_mismatch"])


def enforce_wip(stage: dict, count: int, cfg: dict) -> None:
    if count > stage["wip_limit"]:
        raise Refusal(cfg["refusals"]["wip_exceeded"])


def receipt(item: WorkItem, cfg: dict) -> dict:
    payload = {
        "version": cfg["version"],
        "subject": item.subject,
        "acceptance": item.acceptance,
        "authority": item.authority,
        "reversible": item.reversible,
        "acceptance_mutated": item.acceptance_mutated,
        "actuation_receipted": item.actuation_receipted,
        "replay_match": item.replay_match,
        "zero_unreceipted_actuation": cfg["zero_unreceipted_actuation"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {**payload, "sha256": hashlib.sha256(canonical).hexdigest()}


def run(item: WorkItem, cfg: dict) -> dict:
    validate_config(cfg)
    admit(item, cfg)
    for stage in cfg["stage"]:
        enforce_wip(stage, 1, cfg)
    out = receipt(item, cfg)
    out["standing"] = "ALIVE"
    out["stages"] = [stage["id"] for stage in cfg["stage"]]
    return out


def self_test(cfg: dict) -> None:
    good = WorkItem("0" * 40, "python3 -m unittest tests.test_tpcs_pipeline -v", "CONSTRUCT")
    result = run(good, cfg)
    assert result["standing"] == "ALIVE"
    cases = [
        (WorkItem("not-a-sha", "x", "SELECT"), "REFUSED_INVALID_SUBJECT"),
        (WorkItem("0" * 40, "x", "CONSTRUCT", acceptance_mutated=True), "REFUSED_ACCEPTANCE_MUTATION"),
        (WorkItem("0" * 40, "x", "DO", actuation_receipted=False), "REFUSED_UNRECEIPTED_ACTUATION"),
        (WorkItem("0" * 40, "x", "SELECT", replay_match=False), "REFUSED_REPLAY_MISMATCH"),
    ]
    for item, expected in cases:
        try:
            run(item, cfg)
        except Refusal as exc:
            assert str(exc) == expected, (str(exc), expected)
        else:
            raise AssertionError(f"expected {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Toyota Code Production System admission/verifier")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--subject")
    parser.add_argument("--acceptance")
    parser.add_argument("--authority", choices=["SELECT", "CONSTRUCT", "DO"])
    parser.add_argument("--receipt")
    args = parser.parse_args()
    cfg = load_config()
    if args.self_test:
        self_test(cfg)
        print("TPCS_SELF_TEST_ALIVE")
        return 0
    if not all([args.subject, args.acceptance, args.authority]):
        parser.error("--subject, --acceptance and --authority are required without --self-test")
    result = run(WorkItem(args.subject, args.acceptance, args.authority), cfg)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        Path(args.receipt).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
