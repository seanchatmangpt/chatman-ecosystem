#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "catalog" / "tpcs.toml"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Refusal(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkItem:
    subject: str
    acceptance: str
    authority: str
    work_id: str = ""
    value_stream: str = "default"
    class_of_service: str = "standard"
    value: float = 0.0
    urgency: float = 0.0
    evidence: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    cycle_time: float = 0.0
    age: float = 0.0
    reversible: bool = True
    acceptance_mutated: bool = False
    acceptance_passed: bool = False
    actuation_receipted: bool = True
    replay_match: bool = True
    observed_subject: str | None = None
    andon_active: bool = False

    @property
    def id(self) -> str:
        return self.work_id or self.subject


def load_config(path: Path = CONFIG) -> dict:
    with path.open("rb") as fh:
        return tomllib.load(fh)


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def config_digest(cfg: dict) -> str:
    return canonical_digest(cfg)


def validate_config(cfg: dict) -> None:
    stages = cfg.get("stage", [])
    required = ["observe", "admit", "construct", "verify", "receipt", "replay", "standing"]
    if [s["id"] for s in stages] != required:
        raise ValueError("invalid stage order")
    if cfg.get("mode") != "pull":
        raise ValueError("TPS requires pull flow")
    for forbidden in ("acceptance_mutation_authority", "planner_actuation_authority", "generated_projection_authority"):
        if cfg.get(forbidden):
            raise ValueError(f"{forbidden} must be false")
    if not cfg.get("zero_unreceipted_actuation"):
        raise ValueError("zero unreceipted actuation must be preserved")
    dfcm = cfg.get("dfcm", {})
    if not dfcm.get("preserve_frontier") or dfcm.get("selection") != "deterministic_reversible":
        raise ValueError("DfCM frontier must be preserved with reversible selection")
    if set(dfcm.get("maximize", [])) & set(dfcm.get("minimize", [])):
        raise ValueError("objective cannot be both maximized and minimized")
    if cfg.get("kaizen", {}).get("auto_apply"):
        raise ValueError("kaizen proposals cannot auto-actuate")
    for stage in stages:
        if not isinstance(stage.get("wip_limit"), int) or stage["wip_limit"] < 1:
            raise ValueError(f"invalid WIP limit for {stage['id']}")


def _numeric_dimensions(item: WorkItem, cfg: dict) -> list[float]:
    names = list(cfg["dfcm"]["maximize"]) + list(cfg["dfcm"]["minimize"]) + ["age"]
    return [float(getattr(item, name)) for name in names]


def admit(item: WorkItem, cfg: dict) -> None:
    r = cfg["refusals"]
    if not SHA40.fullmatch(item.subject):
        raise Refusal(r["invalid_subject"])
    if item.observed_subject is not None and item.observed_subject != item.subject:
        raise Refusal(r["identity_drift"])
    if not item.acceptance.strip():
        raise Refusal(r["missing_acceptance"])
    if item.authority not in {"SELECT", "CONSTRUCT", "DO"}:
        raise Refusal(r["invalid_authority"])
    if item.class_of_service not in cfg["class_of_service"]:
        raise Refusal(r["unknown_class"])
    if not item.reversible:
        raise Refusal(r["irreversible_plan"])
    if item.acceptance_mutated:
        raise Refusal(r["acceptance_mutation"])
    if item.authority == "DO" and not item.actuation_receipted:
        raise Refusal(r["unreceipted_actuation"])
    if not item.replay_match:
        raise Refusal(r["replay_mismatch"])
    if item.andon_active and cfg["jidoka"]["andon_blocks_pull"]:
        raise Refusal(r["andon_active"])
    if any(value < 0 for value in _numeric_dimensions(item, cfg)):
        raise Refusal(r["invalid_metric"])


def stage_config(stage_id: str, cfg: dict) -> dict:
    for stage in cfg["stage"]:
        if stage["id"] == stage_id:
            return stage
    raise ValueError(f"unknown stage: {stage_id}")


def enforce_wip(stage: dict, count: int, cfg: dict) -> None:
    if count > stage["wip_limit"]:
        raise Refusal(cfg["refusals"]["wip_exceeded"])


def pull_token(stage_id: str, current_wip: int, cfg: dict, *, andon_active: bool = False) -> dict:
    if andon_active and cfg["jidoka"]["andon_blocks_pull"]:
        raise Refusal(cfg["refusals"]["andon_active"])
    stage = stage_config(stage_id, cfg)
    requested = current_wip + cfg["kanban"]["tokens_per_item"]
    if current_wip < 0 or requested > stage["wip_limit"]:
        raise Refusal(cfg["refusals"]["no_capacity"])
    return {
        "stage": stage_id,
        "token_count": cfg["kanban"]["tokens_per_item"],
        "authority": "SELECT",
        "actuation": False,
        "pull_only": True,
    }


def dominates(a: WorkItem, b: WorkItem, cfg: dict) -> bool:
    no_worse = True
    strictly_better = False
    for name in cfg["dfcm"]["maximize"]:
        av, bv = float(getattr(a, name)), float(getattr(b, name))
        no_worse &= av >= bv
        strictly_better |= av > bv
    for name in cfg["dfcm"]["minimize"]:
        av, bv = float(getattr(a, name)), float(getattr(b, name))
        no_worse &= av <= bv
        strictly_better |= av < bv
    return bool(no_worse and strictly_better)


def pareto_frontier(items: Iterable[WorkItem], cfg: dict) -> list[WorkItem]:
    candidates = list(items)
    if not candidates:
        raise Refusal(cfg["refusals"]["empty_frontier"])
    seen: set[str] = set()
    for item in candidates:
        admit(item, cfg)
        if item.id in seen:
            raise Refusal(cfg["refusals"]["duplicate_work"])
        seen.add(item.id)
    frontier = [
        item for item in candidates
        if not any(other.id != item.id and dominates(other, item, cfg) for other in candidates)
    ]
    if len(frontier) > cfg["dfcm"]["max_frontier"]:
        raise Refusal(cfg["refusals"]["wip_exceeded"])
    return sorted(frontier, key=lambda item: item.id)


def selection_key(item: WorkItem, cfg: dict) -> tuple:
    rank = cfg["class_of_service"][item.class_of_service]["rank"]
    return (
        rank,
        -item.urgency,
        -item.value,
        -item.evidence,
        item.risk,
        item.cost,
        item.cycle_time,
        -item.age,
        item.work_id or item.subject,
        item.subject,
    )


def level_schedule(frontier: Iterable[WorkItem], cfg: dict) -> list[WorkItem]:
    remaining = sorted(frontier, key=lambda item: selection_key(item, cfg))
    scheduled: list[WorkItem] = []
    last_stream: str | None = None
    while remaining:
        alternatives = [item for item in remaining if item.value_stream != last_stream]
        pool = alternatives or remaining
        chosen = min(pool, key=lambda item: selection_key(item, cfg))
        scheduled.append(chosen)
        remaining.remove(chosen)
        last_stream = chosen.value_stream
    return scheduled


def _work_payload(item: WorkItem) -> dict:
    payload = asdict(item)
    payload["work_id"] = item.id
    return payload


def plan(items: Iterable[WorkItem], cfg: dict) -> dict:
    validate_config(cfg)
    candidates = list(items)
    frontier = pareto_frontier(candidates, cfg)
    schedule = level_schedule(frontier, cfg)
    selected = schedule[0]
    inputs = [_work_payload(item) for item in sorted(candidates, key=lambda item: item.id)]
    subjects = sorted({item.subject for item in candidates})
    payload = {
        "version": cfg["version"],
        "config_digest": config_digest(cfg),
        "candidate_count": len(candidates),
        "inputs": inputs,
        "input_digest": canonical_digest(inputs),
        "subjects": subjects,
        "subjects_digest": canonical_digest(subjects),
        "frontier": [item.id for item in frontier],
        "frontier_digest": canonical_digest([item.id for item in frontier]),
        "schedule": [item.id for item in schedule],
        "schedule_digest": canonical_digest([item.id for item in schedule]),
        "selected": selected.id,
        "selection_reversible": True,
        "irreversible_selections": 0,
        "planner_authority": "SELECT",
        "actuation": False,
    }
    return {**payload, "sha256": canonical_digest(payload)}


def verify_plan(record: dict, cfg: dict) -> bool:
    supplied = record.get("sha256")
    payload = {k: v for k, v in record.items() if k != "sha256"}
    if not isinstance(supplied, str) or supplied != canonical_digest(payload):
        return False
    if record.get("config_digest") != config_digest(cfg):
        return False
    if record.get("planner_authority") != "SELECT" or record.get("actuation") is not False:
        return False
    if record.get("selection_reversible") is not True or record.get("irreversible_selections") != 0:
        return False
    inputs = record.get("inputs")
    if not isinstance(inputs, list) or record.get("input_digest") != canonical_digest(inputs):
        return False
    try:
        expected = plan([WorkItem(**row) for row in inputs], cfg)
    except (TypeError, ValueError, Refusal):
        return False
    return expected == record


def flow_metrics(
    available_minutes: float,
    demand_items: float,
    throughput_items_per_minute: float,
    wip_items: float,
    cfg: dict,
) -> dict:
    values = (available_minutes, demand_items, throughput_items_per_minute)
    if any(v <= 0 for v in values) or wip_items < 0:
        raise Refusal(cfg["refusals"]["invalid_metric"])
    takt = available_minutes / demand_items
    cycle = wip_items / throughput_items_per_minute
    return {
        "takt_minutes_per_item": takt,
        "cycle_time_minutes": cycle,
        "wip_items": wip_items,
        "throughput_items_per_minute": throughput_items_per_minute,
        "little_law_reconstructed_wip": throughput_items_per_minute * cycle,
        "meets_takt": (1.0 / throughput_items_per_minute) <= takt,
    }


def bottleneck(
    stage_wip: dict[str, int],
    cfg: dict,
    *,
    throughput: dict[str, float] | None = None,
    defects: dict[str, int] | None = None,
) -> dict:
    throughput = throughput or {}
    defects = defects or {}
    rows: list[tuple[float, float, int, int, str]] = []
    order = {stage["id"]: i for i, stage in enumerate(cfg["stage"])}
    for stage_id, count in stage_wip.items():
        stage = stage_config(stage_id, cfg)
        if count < 0:
            raise Refusal(cfg["refusals"]["invalid_metric"])
        pressure = count / stage["wip_limit"]
        rate = float(throughput.get(stage_id, float("inf")))
        defect_count = int(defects.get(stage_id, 0))
        rows.append((pressure, -rate, defect_count, -order[stage_id], stage_id))
    if not rows:
        raise Refusal(cfg["refusals"]["invalid_metric"])
    pressure, neg_rate, defect_count, _, stage_id = max(rows)
    return {
        "stage": stage_id,
        "pressure": pressure,
        "throughput": None if neg_rate == float("-inf") else -neg_rate,
        "defects": defect_count,
    }


def kaizen_proposal(bottleneck_result: dict, cfg: dict) -> dict | None:
    if bottleneck_result["pressure"] < 0.8 and bottleneck_result["defects"] == 0:
        return None
    return {
        "kind": "capacity-or-input-experiment",
        "target_stage": bottleneck_result["stage"],
        "authority": cfg["kaizen"]["proposal_authority"],
        "reversible": True,
        "auto_apply": False,
        "may_mutate_acceptance": False,
        "may_mutate_wip_limits": False,
    }


def receipt(
    item: WorkItem,
    cfg: dict,
    *,
    frontier_ids: Iterable[str] = (),
    schedule_ids: Iterable[str] = (),
    previous_receipt: str | None = None,
    plan_record: dict | None = None,
) -> dict:
    frontier_ids = list(frontier_ids)
    schedule_ids = list(schedule_ids)
    plan_digest = None
    plan_input_digest = None
    if plan_record is not None:
        if not verify_plan(plan_record, cfg) or item.subject not in plan_record["subjects"]:
            raise Refusal(cfg["refusals"]["invalid_plan_receipt"])
        frontier_ids = list(plan_record["frontier"])
        schedule_ids = list(plan_record["schedule"])
        plan_digest = plan_record["sha256"]
        plan_input_digest = plan_record["input_digest"]
        if previous_receipt is not None and previous_receipt != plan_digest:
            raise Refusal(cfg["refusals"]["invalid_previous_receipt"])
        previous_receipt = plan_digest
    if previous_receipt is not None and not SHA64.fullmatch(previous_receipt):
        raise Refusal(cfg["refusals"]["invalid_previous_receipt"])
    standing = (
        "ALIVE"
        if item.acceptance_passed
        and item.replay_match
        and not item.andon_active
        and (item.authority != "DO" or item.actuation_receipted)
        else "PARTIAL_ALIVE"
    )
    payload = {
        "version": cfg["version"],
        "subject": item.subject,
        "work_id": item.id,
        "acceptance": item.acceptance,
        "acceptance_passed": item.acceptance_passed,
        "authority": item.authority,
        "reversible": item.reversible,
        "acceptance_mutated": item.acceptance_mutated,
        "actuation_receipted": item.actuation_receipted,
        "replay_match": item.replay_match,
        "andon_clear": not item.andon_active,
        "zero_unreceipted_actuation": cfg["zero_unreceipted_actuation"],
        "config_digest": config_digest(cfg),
        "work_digest": canonical_digest(_work_payload(item)),
        "frontier_digest": canonical_digest(frontier_ids),
        "schedule_digest": canonical_digest(schedule_ids),
        "previous_receipt": previous_receipt,
        "plan_digest": plan_digest,
        "plan_input_digest": plan_input_digest,
        "standing": standing,
        "stages": [s["id"] for s in cfg["stage"]],
    }
    return {**payload, "sha256": canonical_digest(payload)}


def verify_receipt(record: dict, cfg: dict) -> bool:
    supplied = record.get("sha256")
    payload = {k: v for k, v in record.items() if k not in {"sha256", "receipt_verified"}}
    return (
        isinstance(supplied, str)
        and supplied == canonical_digest(payload)
        and record.get("config_digest") == config_digest(cfg)
        and record.get("zero_unreceipted_actuation") is True
    )


def run(
    item: WorkItem,
    cfg: dict,
    *,
    frontier_ids: Iterable[str] = (),
    schedule_ids: Iterable[str] = (),
    previous_receipt: str | None = None,
    plan_record: dict | None = None,
) -> dict:
    validate_config(cfg)
    admit(item, cfg)
    for stage in cfg["stage"]:
        enforce_wip(stage, 1, cfg)
    out = receipt(
        item,
        cfg,
        frontier_ids=frontier_ids,
        schedule_ids=schedule_ids,
        previous_receipt=previous_receipt,
        plan_record=plan_record,
    )
    verified = verify_receipt(out, cfg)
    if not verified:
        raise Refusal(cfg["refusals"]["replay_mismatch"])
    return {**out, "receipt_verified": True}


def load_work_items(path: Path) -> list[WorkItem]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw["work_items"] if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        raise ValueError("plan file must be a list or contain work_items")
    return [WorkItem(**row) for row in rows]


def self_test(cfg: dict) -> None:
    good = WorkItem(
        "0" * 40,
        "python3 -m unittest tests.test_tpcs_pipeline -v",
        "CONSTRUCT",
        work_id="self-test",
        acceptance_passed=True,
    )
    assert run(good, cfg)["standing"] == "ALIVE"
    assert run(WorkItem("0" * 40, "x", "SELECT"), cfg)["standing"] == "PARTIAL_ALIVE"
    frontier = pareto_frontier(
        [
            WorkItem("1" * 40, "x", "SELECT", work_id="a", value=10, evidence=10, risk=1, cost=1),
            WorkItem("2" * 40, "x", "SELECT", work_id="b", value=1, evidence=1, risk=9, cost=9),
        ],
        cfg,
    )
    assert [item.id for item in frontier] == ["a"]
    assert plan(frontier, cfg)["irreversible_selections"] == 0
    assert pull_token("construct", 0, cfg)["actuation"] is False
    cases = [
        (WorkItem("not-a-sha", "x", "SELECT"), "REFUSED_INVALID_SUBJECT"),
        (WorkItem("0" * 40, "x", "CONSTRUCT", acceptance_mutated=True), "REFUSED_ACCEPTANCE_MUTATION"),
        (WorkItem("0" * 40, "x", "DO", actuation_receipted=False), "REFUSED_UNRECEIPTED_ACTUATION"),
        (WorkItem("0" * 40, "x", "SELECT", replay_match=False), "REFUSED_REPLAY_MISMATCH"),
        (WorkItem("0" * 40, "x", "SELECT", andon_active=True), "REFUSED_ANDON_ACTIVE"),
    ]
    for item, expected in cases:
        try:
            run(item, cfg)
        except Refusal as exc:
            assert str(exc) == expected
        else:
            raise AssertionError(f"expected {expected}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Toyota Code Production System DfCM control plane")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--subject")
    parser.add_argument("--work-id")
    parser.add_argument("--acceptance")
    parser.add_argument("--authority", choices=["SELECT", "CONSTRUCT", "DO"])
    parser.add_argument("--acceptance-passed", action="store_true")
    parser.add_argument("--previous-receipt")
    parser.add_argument("--from-plan-receipt")
    parser.add_argument("--receipt")
    parser.add_argument("--plan-file")
    parser.add_argument("--plan-receipt")
    parser.add_argument("--metrics", nargs=4, type=float, metavar=("AVAILABLE_MIN", "DEMAND", "THROUGHPUT_PER_MIN", "WIP"))
    args = parser.parse_args()
    cfg = load_config()

    if args.self_test:
        self_test(cfg)
        print("TPCS_SELF_TEST_ALIVE")
        return 0

    if args.plan_file:
        result = plan(load_work_items(Path(args.plan_file)), cfg)
        encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.plan_reccipt:
            Path(args.plan_receipt).write_text(encoded, encoding="utf-8")
        print(encoded, end="")
        return 0

    if args.metrics:
        result = flow_metrics(*args.metrics, cfg)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if not all([args.subject, args.acceptance, args.authority]):
        parser.error("--subject, --acceptance and --authority are required")
    item = WorkItem(
        args.subject,
        args.acceptance,
        args.authority,
        work_id=args.work_id or "",
        acceptance_passed=args.acceptance_passed,
    )
    plan_record = None
    if args.from_plan_receipt:
        plan_record = json.loads(Path(args.from_plan_receipt).read_text(encoding="utf-8"))
    result = run(item, cfg, previous_receipt=args.previous_receipt, plan_record=plan_record)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        Path(args.receipt).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
