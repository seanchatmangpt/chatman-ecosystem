#!/usr/bin/env python3
"""ALOOP-CROWN-001: autonomous-loop qualification crown (RFC-0005).

Consumes lane-authored run records from an ALOOP episode evidence root
(`<root>/lane-*/record.json`) and derives the loop standing as a typed, refusable
verdict. Normative source: engineering-standards
`docs/engineering/rfc/0005-autonomous-loop-qualification.md` + requirements registry
`0005-autonomous-loop-requirements.json`.

Fail-closed: missing or incomplete lane evidence fails every crown term that lane's
evidence would have supported; it is never assumed. Non-self-certification: the crown
reads only `lane-*/record.json` files authored by lanes; it never reads its own
verdicts and refuses an output path inside the evidence root. SELECT/MEASURE only:
no actuation, no authority, no standing promotion (ASSISTED is never promoted).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.0.0"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPLAY_BINDING = re.compile(r"^[A-Za-z0-9_.-]+:[^\s]+$")
EPISODE_STANDINGS = {
    "AUTONOMOUS",
    "ASSISTED",
    "BLOCKED_AUTHORITY",
    "BLOCKED_INFORMATION",
    "FAILED",
    "ALIVE",
    "PARTIAL_ALIVE",
    "BLOCKED",
    "REFUSED",
    "UNSUPPORTED",
    "UNKNOWN",
}
TERMS = (
    "LOOP",
    "CAUSALITY",
    "AUTHORITY",
    "RECEIPTS",
    "RECOVERY",
    "PROVIDERS",
    "OCEL",
    "PROCESS",
    "STRESS",
    "REPLAY",
)
LOOP_CHAIN_STAGES = {"Receipt[n]", "Reobserve[n+1]", "Frontier[n+1]", "WorkOrder[n+1]"}
REQUIRED_OCEL_OBJECT_TYPES = {"Episode", "WorkOrder", "Authority", "Receipt"}
REQUIRED_OCEL_EVENT_CLASSES = {"episode.start", "execution.start", "receipt.persist", "verify"}
RECOVERY_VIAS = {"replan", "reissue", "provider.replace"}
STRESS_KINDS = {"benchmark", "stress", "soak"}
NON_PURPOSE_BRANCHES = {"main", "master"}


class Refusal(ValueError):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"REFUSED[{code}]: {detail}")


def _req_str(record: Dict[str, Any], key: str, lane: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise Refusal("INVALID_RECORD", f"{lane}: field {key!r} must be a non-empty string")
    return value


def validate_record(raw: Any, lane: str) -> Dict[str, Any]:
    """Enforce the RFC-0005 section 7 manifest schema. Refuse, never partially admit."""
    if not isinstance(raw, dict):
        raise Refusal("INVALID_RECORD", f"{lane}: record must be a JSON object")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise Refusal(
            "INVALID_RECORD",
            f"{lane}: schema_version {raw.get('schema_version')!r} != {SCHEMA_VERSION!r}",
        )
    _req_str(raw, "episode", lane)
    if raw.get("lane") != lane:
        raise Refusal("INVALID_RECORD", f"{lane}: record.lane {raw.get('lane')!r} mismatch")
    author = raw.get("author")
    if author != lane:
        raise Refusal(
            "INVALID_RECORD",
            f"{lane}: author {author!r} != lane id (records are lane-authored)",
        )
    _req_str(raw, "objective", lane)
    standing = _req_str(raw, "standing", lane)
    if standing not in EPISODE_STANDINGS:
        raise Refusal("INVALID_RECORD", f"{lane}: standing {standing!r} outside vocabulary")

    repos = raw.get("repos")
    if not isinstance(repos, list) or not repos:
        raise Refusal("INVALID_RECORD", f"{lane}: repos must be a non-empty array")
    for repo in repos:
        if not isinstance(repo, dict):
            raise Refusal("INVALID_RECORD", f"{lane}: repo entry must be an object")
        _req_str(repo, "repo", lane)
        branch = _req_str(repo, "branch", lane)
        if branch.split("/")[-1] in NON_PURPOSE_BRANCHES:
            raise Refusal(
                "INVALID_RECORD", f"{lane}: branch {branch!r} is not a purpose branch"
            )
        for sha_field in ("start_sha", "final_sha"):
            sha = repo.get(sha_field)
            if not isinstance(sha, str) or not SHA40.fullmatch(sha):
                raise Refusal("INVALID_RECORD", f"{lane}: {sha_field} must be a sha40")
        commits = repo.get("commits")
        if not isinstance(commits, list):
            raise Refusal("INVALID_RECORD", f"{lane}: commits must be an array")
        for commit in commits:
            if not isinstance(commit, str) or not SHA40.fullmatch(commit):
                raise Refusal("INVALID_RECORD", f"{lane}: commit {commit!r} must be a sha40")

    for list_field in ("commands", "tests", "falsifiers"):
        entries = raw.get(list_field)
        if not isinstance(entries, list):
            raise Refusal("INVALID_RECORD", f"{lane}: {list_field} must be an array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise Refusal("INVALID_RECORD", f"{lane}: {list_field} entry must be an object")

    receipts = raw.get("receipts")
    if not isinstance(receipts, list):
        raise Refusal("INVALID_RECORD", f"{lane}: receipts must be an array")
    provider_replace = raw.get("provider_replace_admitted", False)
    if not isinstance(provider_replace, bool):
        raise Refusal("INVALID_RECORD", f"{lane}: provider_replace_admitted must be boolean")

    human_edges = raw.get("human_causal_edges")
    if not isinstance(human_edges, list):
        raise Refusal("INVALID_RECORD", f"{lane}: human_causal_edges must be an array")
    for edge in human_edges:
        if not isinstance(edge, dict):
            raise Refusal("INVALID_RECORD", f"{lane}: human causal edge must be an object")
        phase = edge.get("phase")
        if phase not in ("pre-epoch", "post-epoch-execution"):
            raise Refusal("INVALID_RECORD", f"{lane}: human causal edge phase {phase!r} invalid")

    recurrence = raw.get("recurrence")
    if not isinstance(recurrence, dict):
        raise Refusal("INVALID_RECORD", f"{lane}: recurrence must be an object")
    if not isinstance(recurrence.get("demonstrated"), bool):
        raise Refusal("INVALID_RECORD", f"{lane}: recurrence.demonstrated must be boolean")
    if not isinstance(recurrence.get("chain"), list):
        raise Refusal("INVALID_RECORD", f"{lane}: recurrence.chain must be an array")
    iterations = recurrence.get("iterations")
    if not isinstance(iterations, int) or isinstance(iterations, bool) or iterations < 0:
        raise Refusal("INVALID_RECORD", f"{lane}: recurrence.iterations must be a >=0 integer")

    for list_field in ("recovery", "blockers"):
        if not isinstance(raw.get(list_field), list):
            raise Refusal("INVALID_RECORD", f"{lane}: {list_field} must be an array")

    stress = raw.get("stress")
    if not isinstance(stress, dict):
        raise Refusal("INVALID_RECORD", f"{lane}: stress must be an object")
    if stress.get("kind") not in STRESS_KINDS:
        raise Refusal("INVALID_RECORD", f"{lane}: stress.kind must be one of {sorted(STRESS_KINDS)}")
    if stress.get("result") not in ("PASS", "FAIL", "NOT_RUN"):
        raise Refusal("INVALID_RECORD", f"{lane}: stress.result must be PASS|FAIL|NOT_RUN")

    ocel = raw.get("ocel_summary")
    if not isinstance(ocel, dict):
        raise Refusal("INVALID_RECORD", f"{lane}: ocel_summary must be an object")
    for list_field in ("object_types", "event_classes"):
        if not isinstance(ocel.get(list_field), list):
            raise Refusal("INVALID_RECORD", f"{lane}: ocel_summary.{list_field} must be an array")
    count = ocel.get("event_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise Refusal("INVALID_RECORD", f"{lane}: ocel_summary.event_count must be a >=0 integer")

    authority = raw.get("authority")
    if not isinstance(authority, dict):
        raise Refusal("INVALID_RECORD", f"{lane}: authority must be an object")
    _req_str(authority, "origin", lane)
    if not isinstance(authority.get("violations"), list):
        raise Refusal("INVALID_RECORD", f"{lane}: authority.violations must be an array")

    if not isinstance(raw.get("ts"), str) or not raw.get("ts"):
        raise Refusal("INVALID_RECORD", f"{lane}: ts must be a non-empty string")
    return raw


def load_lane_records(root: Path) -> Dict[str, Optional[Dict[str, Any]]]:
    """Discover lane-* directories; absent record.json is typed absence, never skipped."""
    if not root.is_dir():
        raise Refusal("EVIDENCE_ROOT_ABSENT", str(root))
    records: Dict[str, Optional[Dict[str, Any]]] = {}
    for lane_dir in sorted(root.glob("lane-*")):
        if not lane_dir.is_dir():
            continue
        lane = lane_dir.name
        record_path = lane_dir / "record.json"
        if not record_path.is_file():
            records[lane] = None
            continue
        try:
            raw = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Refusal("INVALID_RECORD", f"{lane}: unreadable record.json: {exc}") from exc
        records[lane] = validate_record(raw, lane)
    if not records:
        raise Refusal("NO_LANES", f"no lane-* directories under {root}")
    return records


def _receipt_defects(record: Dict[str, Any]) -> List[str]:
    defects: List[str] = []
    receipts = record.get("receipts", [])
    provider_replace = record.get("provider_replace_admitted", False)
    for index, receipt in enumerate(receipts):
        label = f"{record['lane']}:receipt[{index}]"
        if not isinstance(receipt, dict):
            defects.append(f"{label}: not an object")
            continue
        for field in (
            "work_order_id",
            "provider",
            "provider_execution_id",
            "origin_authority",
            "exit_status",
            "replay_binding",
            "consequence",
        ):
            value = receipt.get(field)
            if not isinstance(value, str) or not value.strip():
                defects.append(f"{label}: missing {field}")
        provider = receipt.get("provider")
        work_order_id = receipt.get("work_order_id", "")
        if isinstance(provider, str) and provider and isinstance(work_order_id, str):
            if provider.lower() in work_order_id.lower():
                raise Refusal(
                    "PROVIDER_NEUTRALITY",
                    f"{label}: work_order_id embeds provider {provider!r}",
                )
        binding = receipt.get("replay_binding")
        if isinstance(binding, str) and binding and not REPLAY_BINDING.fullmatch(binding):
            defects.append(f"{label}: replay_binding {binding!r} not verifier:target shape")
    if receipts and not provider_replace:
        pass  # receipts present is enough; provider diversity handled by PROVIDERS term
    return defects


def evaluate(records: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    terms: Dict[str, Dict[str, Any]] = {
        term: {"passed": True, "missing": [], "violations": []} for term in TERMS
    }

    def fail(term: str, reason: str, *, violation: bool = False) -> None:
        terms[term]["passed"] = False
        bucket = "violations" if violation else "missing"
        terms[term][bucket].append(reason)

    present = {lane: rec for lane, rec in records.items() if rec is not None}
    absent = sorted(lane for lane, rec in records.items() if rec is None)

    # Anti-vacuity: a corpus with zero admitted records supports no term at all.
    if not present:
        for term in TERMS:
            fail(term, "no lane record present (fail-closed: no evidence admitted)")
        missing_terms = sorted(term for term in TERMS if not terms[term]["passed"])
        return {"terms": terms, "missing_terms": missing_terms, "violations": []}

    # Absence taints every term the lane's evidence would have supported (fail-closed).
    for lane in absent:
        for term in TERMS:
            if term in ("LOOP", "RECOVERY", "PROVIDERS", "STRESS"):
                fail(term, f"{lane}: record.json absent")

    # LOOP + CAUSALITY
    autonomy_class_recurrence = False
    for lane, rec in sorted(present.items()):
        tainted = any(
            edge.get("phase") == "post-epoch-execution"
            for edge in rec.get("human_causal_edges", [])
        )
        recurrence = rec.get("recurrence", {})
        chain_ok = LOOP_CHAIN_STAGES.issubset(set(recurrence.get("chain", [])))
        if (
            recurrence.get("demonstrated") is True
            and recurrence.get("iterations", 0) >= 2
            and chain_ok
            and not tainted
        ):
            autonomy_class_recurrence = True
        if tainted and recurrence.get("demonstrated") is True:
            fail(
                "LOOP",
                f"{lane}: recurrence chain carries post-epoch human causality "
                "(automation, not autonomy)",
                violation=True,
            )
        standing = rec.get("standing", "UNKNOWN")
        if tainted and standing == "AUTONOMOUS":
            fail(
                "CAUSALITY",
                f"{lane}: claims AUTONOMOUS over a tainted segment (law L1/L6)",
                violation=True,
            )
        if not tainted and standing == "AUTONOMOUS" and recurrence.get("demonstrated") is not True:
            fail(
                "CAUSALITY",
                f"{lane}: claims AUTONOMOUS without demonstrated recurrence (law L5)",
                violation=True,
            )
    if not autonomy_class_recurrence:
        fail("LOOP", "no lane demonstrates an autonomy-class recurrence chain")

    # AUTHORITY + RECEIPTS + REPLAY (per-record)
    providers_seen = set()
    provider_replace_admitted = False
    for lane, rec in sorted(present.items()):
        authority = rec.get("authority", {})
        if not authority.get("origin"):
            fail("AUTHORITY", f"{lane}: authority.origin undeclared")
        for violation in authority.get("violations", []):
            fail("AUTHORITY", f"{lane}: authority violation: {violation}", violation=True)
        blockers = rec.get("blockers", [])
        for blocker in blockers:
            if isinstance(blocker, dict) and blocker.get("type") == "AUTHORITY_FAILURE":
                fail(
                    "AUTHORITY",
                    f"{lane}: honestly typed block: {blocker.get('detail', '')}",
                )
        actuated = any(
            repo.get("commits") for repo in rec.get("repos", []) if isinstance(repo, dict)
        )
        receipts = rec.get("receipts", [])
        if actuated and not receipts:
            fail("RECEIPTS", f"{lane}: actuation (commits) with zero receipts (law L7)")
        for defect in _receipt_defects(rec):
            if "replay_binding" in defect:
                fail("REPLAY", defect)
            else:
                fail("RECEIPTS", defect)
        for receipt in receipts:
            if isinstance(receipt, dict):
                provider = receipt.get("provider")
                if isinstance(provider, str) and provider:
                    providers_seen.add(provider)
        if rec.get("provider_replace_admitted") is True:
            provider_replace_admitted = True

    # RECOVERY
    witnessed_recovery = False
    for lane, rec in sorted(present.items()):
        for index, entry in enumerate(rec.get("recovery", [])):
            if not isinstance(entry, dict):
                fail("RECOVERY", f"{lane}:recovery[{index}]: not an object")
                continue
            if (
                entry.get("to") == "success"
                and entry.get("via") in RECOVERY_VIAS
                and entry.get("human_edges") == 0
            ):
                witnessed_recovery = True
    if not witnessed_recovery:
        fail("RECOVERY", "no witnessed self-recovery with zero human edges")

    # PROVIDERS
    if not providers_seen:
        fail("PROVIDERS", "no receipt carries a provider")
    if len(providers_seen) < 2 and not provider_replace_admitted:
        fail(
            "PROVIDERS",
            f"INSUFFICIENT_PROVIDER_DIVERSITY: providers={sorted(providers_seen)} "
            "and no provider.replace capability admitted (law L2)",
        )

    # OCEL + PROCESS + STRESS
    stress_pass = False
    for lane, rec in sorted(present.items()):
        ocel = rec.get("ocel_summary", {})
        missing_types = REQUIRED_OCEL_OBJECT_TYPES - set(ocel.get("object_types", []))
        missing_events = REQUIRED_OCEL_EVENT_CLASSES - set(ocel.get("event_classes", []))
        if missing_types or missing_events or ocel.get("event_count", 0) < 1:
            fail(
                "OCEL",
                f"{lane}: ocel_summary incomplete "
                f"(types missing={sorted(missing_types)}, events missing={sorted(missing_events)})",
            )
        for repo in rec.get("repos", []):
            if not isinstance(repo, dict):
                continue
            if repo.get("start_sha") == repo.get("final_sha") and not repo.get("commits"):
                fail(
                    "PROCESS",
                    f"{lane}: {repo.get('repo')}: start==final with no commits "
                    "(read-only objectives must be declared in the record)",
                )
        if rec.get("stress", {}).get("result") == "PASS":
            stress_pass = True
    if not stress_pass:
        fail("STRESS", "no benchmark/stress/soak result PASS on an admitted subject")

    missing_terms = sorted(term for term in TERMS if not terms[term]["passed"])
    violations = sorted(
        reason for term in TERMS for reason in terms[term]["violations"]
    )
    return {"terms": terms, "missing_terms": missing_terms, "violations": violations}


def derive_standing(missing_terms: List[str]) -> str:
    if not missing_terms:
        return "AUTONOMOUS_LOOP_ALIVE"
    return "AUTONOMOUS_LOOP_PARTIAL_ALIVE"


def verdict(records: Dict[str, Optional[Dict[str, Any]]], episode: str, root: Path) -> Dict[str, Any]:
    evaluation = evaluate(records)
    return {
        "crown": "ALOOP-CROWN-001",
        "schema_version": SCHEMA_VERSION,
        "episode": episode,
        "evidence_root": str(root),
        "lanes": {lane: ("ok" if rec is not None else "absent") for lane, rec in sorted(records.items())},
        "terms": evaluation["terms"],
        "missing_terms": evaluation["missing_terms"],
        "violations": evaluation["violations"],
        "standing": derive_standing(evaluation["missing_terms"]),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / ".zcode/workspace/default/aloop-dogfood-001",
        help="episode evidence root containing lane-*/record.json",
    )
    parser.add_argument("--episode", default="ALOOP-ZCODE-DOGFOOD-001")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional verdict output path (never inside the evidence root)",
    )
    args = parser.parse_args(argv)

    root = args.root.expanduser().resolve()
    if args.out is not None:
        out = args.out.expanduser().resolve()
        if root == out or root in out.parents or out == root:
            raise Refusal(
                "SELF_CERTIFICATION",
                f"verdict output {out} must live outside the evidence root {root}",
            )
        for lane_dir in root.glob("lane-*"):
            lane_resolved = lane_dir.resolve()
            if lane_resolved == out or lane_resolved in out.parents:
                raise Refusal(
                    "SELF_CERTIFICATION",
                    f"verdict output {out} must never live inside a lane directory",
                )

    records = load_lane_records(root)
    result = verdict(records, args.episode, root)
    payload = json.dumps(result, sort_keys=True, indent=2, ensure_ascii=True)
    if args.out is not None:
        args.out.expanduser().resolve().write_text(payload + "\n", encoding="utf-8")
    print(payload)
    if result["standing"] == "AUTONOMOUS_LOOP_ALIVE":
        return 0
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Refusal as refusal:
        print(json.dumps({"refusal": refusal.code, "detail": refusal.detail}, sort_keys=True))
        sys.exit(2)
