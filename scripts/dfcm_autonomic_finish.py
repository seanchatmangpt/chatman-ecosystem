#!/usr/bin/env python3
"""Deterministic DFCM autonomic release finisher.

The controller is deliberately powerless with respect to consequential DO.
It selects the highest-relief reversible frontier, manufactures exact-subject
intents, requires an authority broker for DO, evaluates an executable Definition
of Done, and emits hash-chained receipts that can be deterministically replayed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

STANDINGS = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}
REPAIRABLE = {"UNKNOWN", "PARTIAL_ALIVE", "BLOCKED", "BUILD_BROKEN"}


class Refusal(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(f"REFUSED:{code}:{detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Candidate:
    component_id: str
    repository: str
    ref: str
    sha: str
    standing: str
    role: str
    blocker: str | None
    direct_unlocks: int
    transitive_unlocks: int
    reversibility: int
    evidence_cost: int
    authority_cost: int

    @property
    def score(self) -> tuple[int, int, int, int, str]:
        return (
            self.transitive_unlocks,
            self.direct_unlocks,
            self.reversibility,
            -(self.evidence_cost + self.authority_cost),
            self.component_id,
        )


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _components(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = manifest.get("components")
    if not isinstance(rows, list) or not rows:
        raise Refusal("MANIFEST_EMPTY", "components")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise Refusal("COMPONENT_INVALID", repr(row))
        cid = row.get("id")
        if not isinstance(cid, str) or not cid:
            raise Refusal("COMPONENT_ID_INVALID", repr(cid))
        if cid in by_id:
            raise Refusal("DUPLICATE_COMPONENT", cid)
        standing = row.get("standing")
        if standing not in STANDINGS:
            raise Refusal("STANDING_INVALID", f"{cid}:{standing}")
        sha = row.get("sha")
        if (
            not isinstance(sha, str)
            or len(sha) != 40
            or any(c not in "0123456789abcdef" for c in sha)
        ):
            raise Refusal("SHA_INVALID", f"{cid}:{sha}")
        deps = row.get("depends_on")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise Refusal("DEPENDENCIES_INVALID", cid)
        if not isinstance(row.get("repository"), str) or "/" not in row["repository"]:
            raise Refusal("REPOSITORY_INVALID", cid)
        if not isinstance(row.get("ref"), str) or not row["ref"]:
            raise Refusal("REF_INVALID", cid)
        if not isinstance(row.get("role"), str) or not row["role"]:
            raise Refusal("ROLE_INVALID", cid)
        by_id[cid] = row
    for cid, row in by_id.items():
        missing = [dep for dep in row["depends_on"] if dep not in by_id]
        if missing:
            raise Refusal(
                "DEPENDENCY_NOT_ADMITTED", f"{cid}:{','.join(sorted(missing))}"
            )
    _assert_acyclic(by_id)
    return by_id


def _assert_acyclic(by_id: dict[str, dict[str, Any]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(cid: str) -> None:
        if cid in visited:
            return
        if cid in visiting:
            raise Refusal("DEPENDENCY_CYCLE", cid)
        visiting.add(cid)
        for dep in by_id[cid]["depends_on"]:
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)

    for cid in sorted(by_id):
        visit(cid)


def reverse_edges(by_id: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    rev = {cid: set() for cid in by_id}
    for cid, row in by_id.items():
        for dep in row["depends_on"]:
            rev[dep].add(cid)
    return rev


def descendants(cid: str, rev: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(rev[cid])
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(rev[node])
    return seen


def _costs(row: dict[str, Any]) -> tuple[int, int, int]:
    standing = row["standing"]
    blocker = str(row.get("blocker", ""))
    evidence_cost = {
        "BUILD_BROKEN": 1,
        "PARTIAL_ALIVE": 2,
        "UNKNOWN": 3,
        "BLOCKED": 4,
    }.get(standing, 9)
    authority_cost = (
        5
        if any(
            token in blocker.upper()
            for token in ("AUTHORITY", "BILLING", "SPENDING", "CREDENTIAL")
        )
        else 0
    )
    reversibility = (
        3
        if standing in {"BUILD_BROKEN", "PARTIAL_ALIVE"}
        else 2
        if standing == "UNKNOWN"
        else 1
    )
    return reversibility, evidence_cost, authority_cost


def frontier(manifest: dict[str, Any]) -> list[Candidate]:
    by_id = _components(manifest)
    rev = reverse_edges(by_id)
    result: list[Candidate] = []
    for cid, row in by_id.items():
        if not row.get("required", False) or row["standing"] not in REPAIRABLE:
            continue
        if any(by_id[dep]["standing"] != "ALIVE" for dep in row["depends_on"]):
            continue
        desc = descendants(cid, rev)
        direct = sum(
            1
            for child in rev[cid]
            if by_id[child].get("required", False)
            and by_id[child]["standing"] != "ALIVE"
        )
        transitive = sum(
            1
            for child in desc
            if by_id[child].get("required", False)
            and by_id[child]["standing"] != "ALIVE"
        )
        reversibility, evidence_cost, authority_cost = _costs(row)
        result.append(
            Candidate(
                component_id=cid,
                repository=row["repository"],
                ref=row["ref"],
                sha=row["sha"],
                standing=row["standing"],
                role=row["role"],
                blocker=row.get("blocker"),
                direct_unlocks=direct,
                transitive_unlocks=transitive,
                reversibility=reversibility,
                evidence_cost=evidence_cost,
                authority_cost=authority_cost,
            )
        )
    return sorted(result, key=lambda c: c.score, reverse=True)


def action_for(candidate: Candidate) -> str:
    if candidate.standing == "BUILD_BROKEN":
        return "DIAGNOSE_REPAIR_VERIFY"
    if candidate.standing == "BLOCKED":
        return "RECLASSIFY_OR_USE_BOUNDED_ALTERNATE_TRANSPORT"
    if candidate.standing == "PARTIAL_ALIVE":
        return "CLOSE_MISSING_EXACT_EXECUTION_EDGE"
    if candidate.standing == "UNKNOWN":
        return "ORIENT_EXECUTE_CANONICAL_VERIFIER"
    raise Refusal("NO_ACTION", candidate.component_id)


def manufacture_intent(candidate: Candidate, observation_digest: str) -> dict[str, Any]:
    intent = {
        "schema": "urn:chatman:dfcm:intent:v1",
        "subject": {
            "component": candidate.component_id,
            "repository": candidate.repository,
            "ref": candidate.ref,
            "sha": candidate.sha,
        },
        "role": candidate.role,
        "standing_before": candidate.standing,
        "blocker": candidate.blocker,
        "action": action_for(candidate),
        "dfcm": {
            "direct_unlocks": candidate.direct_unlocks,
            "transitive_unlocks": candidate.transitive_unlocks,
            "reversibility": candidate.reversibility,
            "evidence_cost": candidate.evidence_cost,
            "authority_cost": candidate.authority_cost,
        },
        "authority": {
            "select": True,
            "construct": True,
            "do": False,
            "exclusive_do_path": "BRCE",
        },
        "acceptance": [
            "Freeze exact subject before mutation.",
            "Read owning repository doctrine and generated-artifact policy.",
            "Repair the existing lawful path; do not create a parallel authority stack.",
            "Run narrowest owning verifier, then expand only after success.",
            "Preserve typed negative fixtures and refusal behavior.",
            "Bind execution receipt and replay to the same exact subject before ALIVE.",
        ],
        "observation_digest": observation_digest,
    }
    intent["intent_digest"] = digest(intent)
    return intent


def select(manifest: dict[str, Any], limit: int = 1) -> list[dict[str, Any]]:
    if limit < 1:
        raise Refusal("LIMIT_INVALID", str(limit))
    obs_digest = digest(manifest)
    candidates = frontier(manifest)
    return [manufacture_intent(c, obs_digest) for c in candidates[:limit]]


def definition_of_done(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compute release completion from exact admitted evidence, never narrative."""
    by_id = _components(manifest)
    required = {cid: row for cid, row in by_id.items() if row.get("required", False)}
    if not required:
        raise Refusal("DOD_NO_REQUIRED_COMPONENTS", "components")

    required_roles_raw = manifest.get("release", {}).get("required_roles", [])
    if not isinstance(required_roles_raw, list) or not all(
        isinstance(role, str) and role for role in required_roles_raw
    ):
        raise Refusal("DOD_REQUIRED_ROLES_INVALID", repr(required_roles_raw))

    findings: list[dict[str, str]] = []
    checks = {
        "all_required_alive": True,
        "all_execution_receipts_present": True,
        "all_executed_subjects_exact": True,
        "all_dependencies_alive": True,
        "all_required_roles_present": True,
    }
    alive_roles: set[str] = set()

    for cid in sorted(required):
        row = required[cid]
        if row["standing"] != "ALIVE":
            checks["all_required_alive"] = False
            findings.append(
                {
                    "code": "DOD_COMPONENT_NOT_ALIVE",
                    "subject": cid,
                    "detail": row["standing"],
                }
            )
        else:
            alive_roles.add(row["role"])
            receipt_id = row.get("execution_receipt")
            if not isinstance(receipt_id, str) or not receipt_id.strip():
                checks["all_execution_receipts_present"] = False
                findings.append(
                    {
                        "code": "DOD_EXECUTION_RECEIPT_MISSING",
                        "subject": cid,
                        "detail": "ALIVE requires owning execution receipt",
                    }
                )
            if row.get("executed_sha") != row["sha"]:
                checks["all_executed_subjects_exact"] = False
                findings.append(
                    {
                        "code": "DOD_EXECUTED_SUBJECT_DRIFT",
                        "subject": cid,
                        "detail": f"admitted={row['sha']} executed={row.get('executed_sha')}",
                    }
                )
        for dep in row["depends_on"]:
            if by_id[dep]["standing"] != "ALIVE":
                checks["all_dependencies_alive"] = False
                findings.append(
                    {
                        "code": "DOD_DEPENDENCY_NOT_ALIVE",
                        "subject": cid,
                        "detail": f"{dep}:{by_id[dep]['standing']}",
                    }
                )

    for role in sorted(set(required_roles_raw)):
        if role not in alive_roles:
            checks["all_required_roles_present"] = False
            findings.append(
                {
                    "code": "DOD_REQUIRED_ROLE_NOT_ALIVE",
                    "subject": role,
                    "detail": "no required ALIVE component provides this role",
                }
            )

    hard_done = all(checks.values()) and not findings
    declared = manifest.get("release", {}).get("standing", "UNKNOWN")
    if declared not in STANDINGS:
        raise Refusal("DOD_RELEASE_STANDING_INVALID", str(declared))

    declaration_overclaim = declared == "ALIVE" and not hard_done
    if declaration_overclaim:
        findings.append(
            {
                "code": "DOD_RELEASE_STANDING_OVERCLAIM",
                "subject": "release",
                "detail": "declared ALIVE before computed Definition of Done",
            }
        )

    return {
        "schema": "urn:chatman:dfcm:definition-of-done:v1",
        "done": hard_done and not declaration_overclaim,
        "promotion_ready": hard_done and declared != "ALIVE",
        "declared_release_standing": declared,
        "required_component_count": len(required),
        "checks": checks,
        "findings": findings,
    }


def admit_do(intent: dict[str, Any], grant: dict[str, Any] | None) -> dict[str, Any]:
    """Broker admission. Never infers DO authority from capability or credentials."""
    if grant is None:
        raise Refusal("DO_AUTHORITY_MISSING", intent["subject"]["component"])
    required = {
        "subject_sha",
        "intent_digest",
        "scope",
        "expires_at",
        "authority_id",
    }
    if not required.issubset(grant):
        raise Refusal("DO_GRANT_MALFORMED", ",".join(sorted(required - set(grant))))
    if grant["subject_sha"] != intent["subject"]["sha"]:
        raise Refusal("DO_SUBJECT_DRIFT", intent["subject"]["component"])
    if grant["intent_digest"] != intent["intent_digest"]:
        raise Refusal("DO_INTENT_DRIFT", intent["subject"]["component"])
    if grant["scope"] != "BRCE:VERIFY_REPAIR_ONLY":
        raise Refusal("DO_SCOPE_UNSUPPORTED", str(grant["scope"]))
    if not isinstance(grant["authority_id"], str) or not grant["authority_id"].strip():
        raise Refusal("DO_AUTHORITY_ID_INVALID", str(grant["authority_id"]))
    if not isinstance(grant["expires_at"], str) or not grant["expires_at"].strip():
        raise Refusal("DO_EXPIRY_INVALID", str(grant["expires_at"]))
    return {
        "admitted": True,
        "authority_id": grant["authority_id"],
        "scope": grant["scope"],
        "expires_at": grant["expires_at"],
        "subject_sha": grant["subject_sha"],
        "intent_digest": grant["intent_digest"],
    }


def receipt(event: dict[str, Any], previous: str | None = None) -> dict[str, Any]:
    body = {
        "schema": "urn:chatman:dfcm:receipt:v1",
        "previous": previous,
        "event": event,
    }
    body["receipt_digest"] = digest(body)
    return body


def replay_receipts(receipts: Iterable[dict[str, Any]]) -> str:
    previous: str | None = None
    count = 0
    for item in receipts:
        expected = item.get("receipt_digest")
        try:
            body = {k: item[k] for k in ("schema", "previous", "event")}
        except KeyError as exc:
            raise Refusal("RECEIPT_MALFORMED", f"{count}:{exc.args[0]}") from exc
        if item.get("previous") != previous:
            raise Refusal("RECEIPT_CHAIN_BROKEN", str(count))
        if expected != digest(body):
            raise Refusal("RECEIPT_TAMPERED", str(count))
        previous = expected
        count += 1
    return f"ALIVE:REPLAY:{count}:{previous or 'EMPTY'}"


def cycle(manifest: dict[str, Any], limit: int = 1) -> dict[str, Any]:
    dod = definition_of_done(manifest)
    intents: list[dict[str, Any]] = [] if dod["done"] else select(manifest, limit=limit)
    if not dod["done"] and not intents:
        codes = ",".join(sorted({item["code"] for item in dod["findings"]}))
        raise Refusal("NO_LAWFUL_FRONTIER", codes or "definition-of-done-false")

    first = receipt({"phase": "OBSERVE", "manifest_digest": digest(manifest)})
    second = receipt(
        {"phase": "EVALUATE_DOD", "definition_of_done": dod},
        first["receipt_digest"],
    )
    third = receipt(
        {"phase": "SELECT", "intents": intents}, second["receipt_digest"]
    )
    receipts = [first, second, third]
    return {
        "schema": "urn:chatman:dfcm:cycle:v2",
        "standing": "ALIVE" if dod["done"] else "PARTIAL_ALIVE",
        "termination": "DONE" if dod["done"] else "CONTINUE",
        "definition_of_done": dod,
        "intents": intents,
        "receipts": receipts,
        "replay": replay_receipts(receipts),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml")
    )
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument(
        "--definition-of-done",
        action="store_true",
        help="Print the executable Definition of Done; exit 0 when done, 3 otherwise.",
    )
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        if args.definition_of_done:
            result = definition_of_done(manifest)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["done"] else 3
        result = cycle(manifest, args.limit)
    except Refusal as exc:
        print(
            json.dumps(
                {"standing": "REFUSED", "code": exc.code, "detail": exc.detail},
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
