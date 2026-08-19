#!/usr/bin/env python3
"""Deterministic DFCM autonomic release finisher.

The controller is deliberately powerless with respect to consequential DO.
It selects the highest-relief reversible frontier, manufactures exact-subject
intents, requires an authority broker for DO, and emits hash-chained receipts
that can be replayed byte-for-byte from the same admitted observation.
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
    "UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"
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
        # Lexicographic DFCM: preserve/maximize lawful possibilities first,
        # then prefer reversible, low-evidence-cost, low-authority-cost work.
        return (
            self.transitive_unlocks,
            self.direct_unlocks,
            self.reversibility,
            -(self.evidence_cost + self.authority_cost),
            self.component_id,
        )


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


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
        if not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            raise Refusal("SHA_INVALID", f"{cid}:{sha}")
        deps = row.get("depends_on")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise Refusal("DEPENDENCIES_INVALID", cid)
        by_id[cid] = row
    for cid, row in by_id.items():
        missing = [dep for dep in row["depends_on"] if dep not in by_id]
        if missing:
            raise Refusal("DEPENDENCY_NOT_ADMITTED", f"{cid}:{','.join(sorted(missing))}")
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
    evidence_cost = {"BUILD_BROKEN": 1, "PARTIAL_ALIVE": 2, "UNKNOWN": 3, "BLOCKED": 4}.get(standing, 9)
    authority_cost = 5 if any(
        token in blocker.upper() for token in ("AUTHORITY", "BILLING", "SPENDING", "CREDENTIAL")
    ) else 0
    reversibility = 3 if standing in {"BUILD_BROKEN", "PARTIAL_ALIVE"} else 2 if standing == "UNKNOWN" else 1
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
            1 for child in rev[cid]
            if by_id[child].get("required", False) and by_id[child]["standing"] != "ALIVE"
        )
        transitive = sum(
            1 for child in desc
            if by_id[child].get("required", False) and by_id[child]["standing"] != "ALIVE"
        )
        reversibility, evidence_cost, authority_cost = _costs(row)
        result.append(Candidate(
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
        ))
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


def admit_do(intent: dict[str, Any], grant: dict[str, Any] | None) -> dict[str, Any]:
    """Broker admission. Never infers DO authority from capability or credentials."""
    if grant is None:
        raise Refusal("DO_AUTHORITY_MISSING", intent["subject"]["component"])
    required = {"subject_sha", "intent_digest", "scope", "expires_at", "authority_id"}
    if not required.issubset(grant):
        raise Refusal("DO_GRANT_MALFORMED", ",".join(sorted(required - set(grant))))
    if grant["subject_sha"] != intent["subject"]["sha"]:
        raise Refusal("DO_SUBJECT_DRIFT", intent["subject"]["component"])
    if grant["intent_digest"] != intent["intent_digest"]:
        raise Refusal("DO_INTENT_DRIFT", intent["subject"]["component"])
    if grant["scope"] != "BRCE:VERIFY_REPAIR_ONLY":
        raise Refusal("DO_SCOPE_UNSUPPORTED", str(grant["scope"]))
    return {
        "admitted": True,
        "authority_id": grant["authority_id"],
        "scope": grant["scope"],
        "expires_at": grant["expires_at"],
        "subject_sha": grant["subject_sha"],
        "intent_digest": grant["intent_digest"],
    }


def receipt(event: dict[str, Any], previous: str | None = None) -> dict[str, Any]:
    body = {"schema": "urn:chatman:dfcm:receipt:v1", "previous": previous, "event": event}
    body["receipt_digest"] = digest(body)
    return body


def replay_receipts(receipts: Iterable[dict[str, Any]]) -> str:
    previous: str | None = None
    count = 0
    for item in receipts:
        expected = item.get("receipt_digest")
        body = {k: item[k] for k in ("schema", "previous", "event")}
        if item.get("previous") != previous:
            raise Refusal("RECEIPT_CHAIN_BROKEN", str(count))
        if expected != digest(body):
            raise Refusal("RECEIPT_TAMPERED", str(count))
        previous = expected
        count += 1
    return f"ALIVE:REPLAY:{count}:{previous or 'EMPTY'}"


def cycle(manifest: dict[str, Any], limit: int = 1) -> dict[str, Any]:
    intents = select(manifest, limit=limit)
    first = receipt({"phase": "OBSERVE", "manifest_digest": digest(manifest)})
    second = receipt({"phase": "SELECT", "intents": intents}, first["receipt_digest"])
    standing = "ALIVE" if intents else "ALIVE:NO_REPAIRABLE_FRONTIER"
    return {
        "schema": "urn:chatman:dfcm:cycle:v1",
        "standing": standing,
        "intents": intents,
        "receipts": [first, second],
        "replay": replay_receipts([first, second]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml"))
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args(argv)
    try:
        result = cycle(load_manifest(args.manifest), args.limit)
    except Refusal as exc:
        print(json.dumps({"standing": "REFUSED", "code": exc.code, "detail": exc.detail}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
