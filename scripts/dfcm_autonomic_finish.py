#!/usr/bin/env python3
"""Post-AGI DfCM execution-capsule controller.

This module closes the gap between reversible DfCM planning and consequential
execution without granting ambient DO authority. It preserves the complete
lawful frontier, fences irreversible edges, manufactures exact-subject intents,
admits only time-bounded BRCE grants, binds observed execution evidence, and
replays a tamper-evident evidence chain.

It never performs consequential DO. External actuators remain responsible for
mutation; this controller only manufactures and validates the control artifacts
that make such mutation admissible and auditable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
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
BRCE_SCOPE = "BRCE:VERIFY_REPAIR_ONLY"


class Refusal(RuntimeError):
    """Typed fail-closed refusal."""

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
    role: str
    standing: str
    blocker: str | None
    dependencies: tuple[str, ...]
    missing_alive_dependencies: tuple[str, ...]
    direct_unlocks: int
    transitive_unlocks: int
    reversibility: int
    evidence_cost: int
    authority_cost: int

    @property
    def actionable(self) -> bool:
        return self.standing in REPAIRABLE and not self.missing_alive_dependencies

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
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    """Backward-compatible SHA-256 control identity; never a canonical Crown receipt."""
    return hashlib.sha256(canonical(value)).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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

        repository = row.get("repository")
        if not isinstance(repository, str) or "/" not in repository:
            raise Refusal("REPOSITORY_INVALID", cid)
        ref = row.get("ref")
        if not isinstance(ref, str) or not ref:
            raise Refusal("REF_INVALID", cid)
        role = row.get("role")
        if not isinstance(role, str) or not role:
            raise Refusal("ROLE_INVALID", cid)
        deps = row.get("depends_on")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise Refusal("DEPENDENCIES_INVALID", cid)
        by_id[cid] = row

    for cid, row in by_id.items():
        missing = sorted(dep for dep in row["depends_on"] if dep not in by_id)
        if missing:
            raise Refusal("DEPENDENCY_NOT_ADMITTED", f"{cid}:{','.join(missing)}")
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
    edges = {cid: set() for cid in by_id}
    for cid, row in by_id.items():
        for dep in row["depends_on"]:
            edges[dep].add(cid)
    return edges


def descendants(cid: str, reverse: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = sorted(reverse[cid], reverse=True)
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(sorted(reverse[node], reverse=True))
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


def candidates(manifest: dict[str, Any]) -> list[Candidate]:
    """Return every required non-ALIVE edge; blocked edges are preserved, not erased."""
    by_id = _components(manifest)
    reverse = reverse_edges(by_id)
    result: list[Candidate] = []
    for cid in sorted(by_id):
        row = by_id[cid]
        if not row.get("required", False) or row["standing"] == "ALIVE":
            continue
        missing = tuple(
            sorted(dep for dep in row["depends_on"] if by_id[dep]["standing"] != "ALIVE")
        )
        desc = descendants(cid, reverse)
        direct = sum(
            1
            for child in reverse[cid]
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
                role=row["role"],
                standing=row["standing"],
                blocker=row.get("blocker"),
                dependencies=tuple(row["depends_on"]),
                missing_alive_dependencies=missing,
                direct_unlocks=direct,
                transitive_unlocks=transitive,
                reversibility=reversibility,
                evidence_cost=evidence_cost,
                authority_cost=authority_cost,
            )
        )
    return result


def action_for(candidate: Candidate) -> str:
    if candidate.standing == "BUILD_BROKEN":
        return "DIAGNOSE_REPAIR_VERIFY"
    if candidate.standing == "BLOCKED":
        return "RECLASSIFY_OR_USE_BOUNDED_ALTERNATE_TRANSPORT"
    if candidate.standing == "PARTIAL_ALIVE":
        return "CLOSE_MISSING_EXACT_EXECUTION_EDGE"
    if candidate.standing == "UNKNOWN":
        return "ORIENT_EXECUTE_CANONICAL_VERIFIER"
    if candidate.standing == "UNSUPPORTED":
        return "PRESERVE_UNSUPPORTED_EDGE"
    raise Refusal("NO_ACTION", candidate.component_id)


def candidate_record(candidate: Candidate) -> dict[str, Any]:
    return {
        "component": candidate.component_id,
        "repository": candidate.repository,
        "ref": candidate.ref,
        "sha": candidate.sha,
        "role": candidate.role,
        "standing": candidate.standing,
        "blocker": candidate.blocker,
        "dependencies": list(candidate.dependencies),
        "missing_alive_dependencies": list(candidate.missing_alive_dependencies),
        "actionable": candidate.actionable,
        "action": action_for(candidate),
        "score": {
            "direct_unlocks": candidate.direct_unlocks,
            "transitive_unlocks": candidate.transitive_unlocks,
            "reversibility": candidate.reversibility,
            "evidence_cost": candidate.evidence_cost,
            "authority_cost": candidate.authority_cost,
        },
    }


def preserve(manifest: dict[str, Any]) -> dict[str, Any]:
    """Preserve the maximal reversible topology before any selection."""
    all_candidates = candidates(manifest)
    actionable = sorted(
        (item for item in all_candidates if item.actionable),
        key=lambda item: item.score,
        reverse=True,
    )
    blocked = sorted(
        (item for item in all_candidates if not item.actionable),
        key=lambda item: item.component_id,
    )
    return {
        "schema": "urn:chatman:dfcm:preserved-frontier:v1",
        "manifest_digest": digest(manifest),
        "policy": "preserve-maximal-reversible-lawful-topology-before-selection",
        "actionable": [candidate_record(item) for item in actionable],
        "blocked": [candidate_record(item) for item in blocked],
        "selection_performed": False,
        "consequential_do_performed": False,
    }


def frontier(manifest: dict[str, Any]) -> list[Candidate]:
    """Backward-compatible actionable frontier ordered by DfCM relief score."""
    return sorted(
        (item for item in candidates(manifest) if item.actionable),
        key=lambda item: item.score,
        reverse=True,
    )


def select(manifest: dict[str, Any], limit: int = 1) -> list[dict[str, Any]]:
    """Backward-compatible deterministic selection after preserving the full frontier."""
    if limit < 1:
        raise Refusal("LIMIT_INVALID", str(limit))
    manifest_digest = digest(manifest)
    return [manufacture_intent(item, manifest_digest) for item in frontier(manifest)[:limit]]


def manufacture_intent(candidate: Candidate, manifest_digest: str) -> dict[str, Any]:
    intent = {
        "schema": "urn:chatman:dfcm:intent:v2",
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
        "calculus": candidate_record(candidate)["score"],
        "dfcm": candidate_record(candidate)["score"],
        "authority": {
            "select": True,
            "construct": True,
            "do": False,
            "exclusive_do_path": "BRCE",
        },
        "fences": [
            "exact-subject identity is frozen",
            "dependency closure must remain ALIVE",
            "generated projections are not source authority",
            "planner/model/proof/hook output grants no DO authority",
            "one failed edge is topology, not graph failure",
            "replay must not re-actuate",
        ],
        "acceptance": [
            "Read owning repository doctrine and generated-artifact policy.",
            "Repair the existing lawful path; do not create a parallel authority stack.",
            "Run the narrowest owning verifier before broader validation.",
            "Preserve typed negative fixtures and refusal behavior.",
            "Bind observed execution to this exact SHA and intent digest.",
            "Require an owning verifier receipt and deterministic replay before ALIVE eligibility.",
        ],
        "manifest_digest": manifest_digest,
    }
    intent["intent_digest"] = digest(intent)
    return intent


def definition_of_done(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compute completion from exact admitted evidence; narrative cannot promote standing."""
    by_id = _components(manifest)
    required = {cid: row for cid, row in by_id.items() if row.get("required", False)}
    if not required:
        raise Refusal("DOD_NO_REQUIRED_COMPONENTS", "components")

    release = manifest.get("release", {})
    required_roles = release.get("required_roles", [])
    if not isinstance(required_roles, list) or not all(
        isinstance(role, str) and role for role in required_roles
    ):
        raise Refusal("DOD_REQUIRED_ROLES_INVALID", repr(required_roles))

    checks = {
        "all_required_alive": True,
        "all_execution_receipts_present": True,
        "all_executed_subjects_exact": True,
        "all_dependencies_alive": True,
        "all_required_roles_present": True,
    }
    findings: list[dict[str, str]] = []
    alive_roles: set[str] = set()

    for cid in sorted(required):
        row = required[cid]
        if row["standing"] != "ALIVE":
            checks["all_required_alive"] = False
            findings.append({"code": "DOD_COMPONENT_NOT_ALIVE", "subject": cid, "detail": row["standing"]})
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

    for role in sorted(set(required_roles)):
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
    declared = release.get("standing", "UNKNOWN")
    if declared not in STANDINGS:
        raise Refusal("DOD_RELEASE_STANDING_INVALID", str(declared))
    if declared == "ALIVE" and not hard_done:
        findings.append(
            {
                "code": "DOD_RELEASE_STANDING_OVERCLAIM",
                "subject": "release",
                "detail": "declared ALIVE before computed Definition of Done",
            }
        )

    return {
        "schema": "urn:chatman:dfcm:definition-of-done:v2",
        "done": hard_done and not findings,
        "promotion_ready": hard_done and declared != "ALIVE",
        "declared_release_standing": declared,
        "required_component_count": len(required),
        "checks": checks,
        "findings": findings,
    }


def construct_capsule(manifest: dict[str, Any], limit: int = 1) -> dict[str, Any]:
    if limit < 1:
        raise Refusal("LIMIT_INVALID", str(limit))

    preserved = preserve(manifest)
    dod = definition_of_done(manifest)
    actionable = frontier(manifest)
    selected = actionable[:limit] if not dod["done"] else []
    manifest_digest = preserved["manifest_digest"]
    intents = [manufacture_intent(item, manifest_digest) for item in selected]

    if not dod["done"] and not intents:
        codes = sorted({item["code"] for item in dod["findings"]})
        raise Refusal("NO_LAWFUL_FRONTIER", ",".join(codes) or "definition-of-done-false")

    capsule: dict[str, Any] = {
        "schema": "urn:chatman:dfcm:execution-capsule:v1",
        "standing": "PARTIAL_ALIVE",
        "target_definition_of_done": "ALIVE" if dod["done"] else "NOT_ALIVE",
        "termination": "DONE" if dod["done"] else "CONTINUE",
        "identity": {
            "manifest_digest": manifest_digest,
            "selected_subjects": [intent["subject"] for intent in intents],
        },
        "preserve": preserved,
        "fence": {
            "chesterton": "no boundary is removed until its protected invariant is identified",
            "authority_ceiling": "SELECT+CONSTRUCT",
            "exclusive_do_path": "BRCE",
            "zero_unreceipted_actuation": True,
            "replay_reactuates": False,
        },
        "calculus": {
            "objects": [candidate_record(item) for item in candidates(manifest)],
            "morphisms": [
                {"from": dep, "to": cid, "kind": "depends_on"}
                for cid, row in sorted(_components(manifest).items())
                for dep in sorted(row["depends_on"])
            ],
            "admission": "dependencies ALIVE + exact subject + typed standing",
            "closure": "all required roles/components + receipts + exact executed SHA",
            "authority": "capability != authority; DO requires exact BRCE grant",
            "actuation": "external only; this controller cannot mutate consequential targets",
            "receipt": "execution evidence binds subject+intent+authority+postcondition",
            "replay": "hash-chain verification never re-actuates",
        },
        "exclusions": [
            "no ambient DO authority",
            "no ALIVE from planner output, prose, compilation, workflow existence, or HTTP success alone",
            "no standing transfer across SHA, repository, environment, or verifier identity drift",
            "no generated projection hand-edit as source authority",
            "no global graph failure from one blocked edge",
        ],
        "falsifiers": [
            "exact subject moved",
            "dependency ceased to be ALIVE",
            "grant missing, malformed, expired, premature, or scope-mismatched",
            "execution evidence does not bind the admitted intent",
            "owning verifier or postcondition fails",
            "replay chain differs or is tampered",
        ],
        "extension": {
            "allowed": "add new objects/morphisms/capabilities without widening existing authority",
            "forbidden": "implicit dependency, ambient authority, or silent semantic fork",
        },
        "operationalization": {
            "selected_intents": intents,
            "selected_count": len(intents),
            "preserved_unselected_count": max(0, len(actionable) - len(intents)),
            "consequential_do_performed": False,
            "next_transition": "BRCE_ADMISSION" if intents else "NONE",
        },
        "definition_of_done": dod,
    }
    unsigned = dict(capsule)
    capsule["capsule_digest"] = digest(unsigned)
    return capsule


def _parse_rfc3339(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise Refusal("DO_TIME_INVALID", field)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise Refusal("DO_TIME_INVALID", field) from exc
    if parsed.tzinfo is None:
        raise Refusal("DO_TIMEZONE_REQUIRED", field)
    return parsed.astimezone(timezone.utc)


def _intent_by_digest(capsule: dict[str, Any], intent_digest: str) -> dict[str, Any]:
    intents = capsule.get("operationalization", {}).get("selected_intents", [])
    if not isinstance(intents, list):
        raise Refusal("CAPSULE_INTENTS_INVALID", "selected_intents")
    for intent in intents:
        if isinstance(intent, dict) and intent.get("intent_digest") == intent_digest:
            return intent
    raise Refusal("DO_INTENT_NOT_SELECTED", str(intent_digest))


def _verify_self_digest(value: dict[str, Any], field: str, code: str) -> None:
    expected = value.get(field)
    if not isinstance(expected, str):
        raise Refusal(code, f"missing:{field}")
    unsigned = {key: item for key, item in value.items() if key != field}
    if expected != digest(unsigned):
        raise Refusal(code, "digest-mismatch")


def verify_capsule(capsule: dict[str, Any]) -> None:
    if capsule.get("schema") != "urn:chatman:dfcm:execution-capsule:v1":
        raise Refusal("CAPSULE_SCHEMA_INVALID", str(capsule.get("schema")))
    _verify_self_digest(capsule, "capsule_digest", "CAPSULE_TAMPERED")
    operational = capsule.get("operationalization")
    if not isinstance(operational, dict) or operational.get("consequential_do_performed") is not False:
        raise Refusal("CAPSULE_AMBIENT_DO", "operationalization")
    fence = capsule.get("fence")
    if not isinstance(fence, dict) or fence.get("exclusive_do_path") != "BRCE":
        raise Refusal("CAPSULE_BRCE_FENCE_INVALID", "exclusive_do_path")


def verify_admission(admission: dict[str, Any]) -> None:
    if admission.get("schema") != "urn:chatman:brce:admission:v1":
        raise Refusal("ADMISSION_SCHEMA_INVALID", str(admission.get("schema")))
    _verify_self_digest(admission, "admission_digest", "ADMISSION_TAMPERED")
    if admission.get("admitted") is not True:
        raise Refusal("EXECUTION_WITHOUT_ADMISSION", "admitted=false")
    if admission.get("consequential_do_performed") is not False:
        raise Refusal("ADMISSION_AMBIENT_DO", "controller-do=true")


def admit_grant(
    capsule: dict[str, Any],
    grant: dict[str, Any] | None,
    *,
    now: str,
) -> dict[str, Any]:
    """Admit a time-bounded BRCE grant for one selected intent; never execute it."""
    verify_capsule(capsule)
    if grant is None:
        raise Refusal("DO_AUTHORITY_MISSING", "grant")
    required = {
        "authority_id",
        "actor",
        "capsule_digest",
        "subject_sha",
        "intent_digest",
        "scope",
        "issued_at",
        "not_before",
        "expires_at",
    }
    missing = sorted(required - set(grant))
    if missing:
        raise Refusal("DO_GRANT_MALFORMED", ",".join(missing))

    if grant["capsule_digest"] != capsule.get("capsule_digest"):
        raise Refusal("DO_CAPSULE_DRIFT", str(grant["capsule_digest"]))
    intent = _intent_by_digest(capsule, str(grant["intent_digest"]))
    if grant["subject_sha"] != intent["subject"]["sha"]:
        raise Refusal("DO_SUBJECT_DRIFT", intent["subject"]["component"])
    if grant["scope"] != BRCE_SCOPE:
        raise Refusal("DO_SCOPE_UNSUPPORTED", str(grant["scope"]))
    if not isinstance(grant["authority_id"], str) or not grant["authority_id"].strip():
        raise Refusal("DO_AUTHORITY_ID_INVALID", str(grant["authority_id"]))
    if not isinstance(grant["actor"], str) or not grant["actor"].strip():
        raise Refusal("DO_ACTOR_INVALID", str(grant["actor"]))

    current = _parse_rfc3339(now, "now")
    issued = _parse_rfc3339(grant["issued_at"], "issued_at")
    not_before = _parse_rfc3339(grant["not_before"], "not_before")
    expires = _parse_rfc3339(grant["expires_at"], "expires_at")
    if issued > not_before:
        raise Refusal("DO_GRANT_WINDOW_INVALID", "issued_at>not_before")
    if not_before >= expires:
        raise Refusal("DO_GRANT_WINDOW_INVALID", "not_before>=expires_at")
    if current < not_before:
        raise Refusal("DO_GRANT_NOT_YET_VALID", grant["not_before"])
    if current >= expires:
        raise Refusal("DO_GRANT_EXPIRED", grant["expires_at"])

    admission: dict[str, Any] = {
        "schema": "urn:chatman:brce:admission:v1",
        "admitted": True,
        "authority_id": grant["authority_id"],
        "actor": grant["actor"],
        "scope": grant["scope"],
        "issued_at": grant["issued_at"],
        "not_before": grant["not_before"],
        "expires_at": grant["expires_at"],
        "capsule_digest": grant["capsule_digest"],
        "subject_sha": grant["subject_sha"],
        "intent_digest": grant["intent_digest"],
        "action": intent["action"],
        "consequential_do_performed": False,
    }
    admission["admission_digest"] = digest(admission)
    return admission


def admit_do(intent: dict[str, Any], grant: dict[str, Any] | None) -> dict[str, Any]:
    """Backward-compatible grant check for the v1 intent-only interface.

    This method deliberately does not consult wall-clock time because its historical
    contract had no admitted observation time. New callers should use ``admit_grant``
    with an execution capsule and explicit ``now`` for deterministic expiry checks.
    """
    if grant is None:
        raise Refusal("DO_AUTHORITY_MISSING", intent["subject"]["component"])
    required = {"subject_sha", "intent_digest", "scope", "expires_at", "authority_id"}
    missing = sorted(required - set(grant))
    if missing:
        raise Refusal("DO_GRANT_MALFORMED", ",".join(missing))
    if grant["subject_sha"] != intent["subject"]["sha"]:
        raise Refusal("DO_SUBJECT_DRIFT", intent["subject"]["component"])
    if grant["intent_digest"] != intent["intent_digest"]:
        raise Refusal("DO_INTENT_DRIFT", intent["subject"]["component"])
    if grant["scope"] != BRCE_SCOPE:
        raise Refusal("DO_SCOPE_UNSUPPORTED", str(grant["scope"]))
    if not isinstance(grant["authority_id"], str) or not grant["authority_id"].strip():
        raise Refusal("DO_AUTHORITY_ID_INVALID", str(grant["authority_id"]))
    if not isinstance(grant["expires_at"], str) or not grant["expires_at"].strip():
        raise Refusal("DO_EXPIRY_INVALID", str(grant["expires_at"]))
    return {
        "admitted": True,
        "legacy_temporal_validity": "UNVERIFIED",
        "consequential_do_performed": False,
        "authority_id": grant["authority_id"],
        "scope": grant["scope"],
        "expires_at": grant["expires_at"],
        "subject_sha": grant["subject_sha"],
        "intent_digest": grant["intent_digest"],
    }


def receipt(event: dict[str, Any], previous: str | None = None) -> dict[str, Any]:
    """Backward-compatible deterministic planning receipt."""
    body = {"schema": "urn:chatman:dfcm:receipt:v1", "previous": previous, "event": event}
    body["receipt_digest"] = digest(body)
    return body


def replay_receipts(receipts: Iterable[dict[str, Any]]) -> str:
    previous: str | None = None
    count = 0
    for item in receipts:
        if not isinstance(item, dict):
            raise Refusal("RECEIPT_MALFORMED", str(count))
        body = {
            "schema": item.get("schema"),
            "previous": item.get("previous"),
            "event": item.get("event"),
        }
        if item.get("previous") != previous:
            raise Refusal("RECEIPT_CHAIN_BROKEN", str(count))
        if item.get("receipt_digest") != digest(body):
            raise Refusal("RECEIPT_TAMPERED", str(count))
        previous = item["receipt_digest"]
        count += 1
    return f"ALIVE:REPLAY:{count}:{previous or 'EMPTY'}"


def cycle(manifest: dict[str, Any], limit: int = 1) -> dict[str, Any]:
    """Backward-compatible planning cycle; never performs DO."""
    dod = definition_of_done(manifest)
    intents = [] if dod["done"] else select(manifest, limit=limit)
    if not dod["done"] and not intents:
        codes = ",".join(sorted({item["code"] for item in dod["findings"]}))
        raise Refusal("NO_LAWFUL_FRONTIER", codes or "definition-of-done-false")
    first = receipt({"phase": "OBSERVE", "manifest_digest": digest(manifest)})
    second = receipt(
        {"phase": "EVALUATE_DOD", "definition_of_done": dod},
        first["receipt_digest"],
    )
    third = receipt({"phase": "SELECT", "intents": intents}, second["receipt_digest"])
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


def evidence_event(kind: str, payload: dict[str, Any], previous: str | None = None) -> dict[str, Any]:
    body = {
        "schema": "urn:chatman:dfcm:evidence-event:v1",
        "previous": previous,
        "kind": kind,
        "payload": payload,
    }
    body["event_digest"] = digest(body)
    return body


def replay_evidence(events: Iterable[dict[str, Any]]) -> str:
    previous: str | None = None
    count = 0
    for event in events:
        if not isinstance(event, dict):
            raise Refusal("EVIDENCE_EVENT_INVALID", str(count))
        expected = event.get("event_digest")
        body = {
            "schema": event.get("schema"),
            "previous": event.get("previous"),
            "kind": event.get("kind"),
            "payload": event.get("payload"),
        }
        if event.get("previous") != previous:
            raise Refusal("EVIDENCE_CHAIN_BROKEN", str(count))
        if expected != digest(body):
            raise Refusal("EVIDENCE_TAMPERED", str(count))
        previous = expected
        count += 1
    return f"ALIVE:REPLAY:{count}:{previous or 'EMPTY'}"


def close_execution(
    capsule: dict[str, Any],
    admission: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Bind already-observed execution to exact identity. This does not actuate."""
    verify_capsule(capsule)
    verify_admission(admission)
    if admission.get("capsule_digest") != capsule.get("capsule_digest"):
        raise Refusal("EXECUTION_CAPSULE_DRIFT", str(admission.get("capsule_digest")))

    required = {
        "subject_sha",
        "intent_digest",
        "exit_code",
        "postcondition_verified",
        "verifier",
        "verifier_receipt",
        "observed_at",
        "changed",
        "verified",
        "replay",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise Refusal("EXECUTION_EVIDENCE_MALFORMED", ",".join(missing))
    if evidence["subject_sha"] != admission.get("subject_sha"):
        raise Refusal("EXECUTION_SUBJECT_DRIFT", str(evidence["subject_sha"]))
    if evidence["intent_digest"] != admission.get("intent_digest"):
        raise Refusal("EXECUTION_INTENT_DRIFT", str(evidence["intent_digest"]))
    if not isinstance(evidence["exit_code"], int):
        raise Refusal("EXECUTION_EXIT_CODE_INVALID", repr(evidence["exit_code"]))
    if evidence["exit_code"] != 0:
        raise Refusal("EXECUTION_FAILED", str(evidence["exit_code"]))
    if evidence["postcondition_verified"] is not True:
        raise Refusal("POSTCONDITION_NOT_VERIFIED", "false")
    for field in ("verifier", "verifier_receipt", "observed_at"):
        if not isinstance(evidence[field], str) or not evidence[field].strip():
            raise Refusal("EXECUTION_EVIDENCE_FIELD_INVALID", field)
    observed_at = _parse_rfc3339(evidence["observed_at"], "observed_at")
    not_before = _parse_rfc3339(admission.get("not_before"), "not_before")
    expires_at = _parse_rfc3339(admission.get("expires_at"), "expires_at")
    if observed_at < not_before:
        raise Refusal("EXECUTION_BEFORE_AUTHORITY_WINDOW", evidence["observed_at"])
    if observed_at >= expires_at:
        raise Refusal("EXECUTION_AFTER_AUTHORITY_EXPIRY", evidence["observed_at"])
    for field in ("changed", "verified", "replay"):
        value = evidence[field]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise Refusal("EXECUTION_EVIDENCE_FIELD_INVALID", field)
    if not evidence["verified"]:
        raise Refusal("EXECUTION_VERIFICATION_EMPTY", "verified")
    if not evidence["replay"]:
        raise Refusal("EXECUTION_REPLAY_EMPTY", "replay")

    first = evidence_event(
        "ADMISSION",
        {
            "admission_digest": admission.get("admission_digest"),
            "authority_id": admission.get("authority_id"),
            "actor": admission.get("actor"),
            "scope": admission.get("scope"),
            "subject_sha": admission.get("subject_sha"),
            "intent_digest": admission.get("intent_digest"),
        },
    )
    second = evidence_event(
        "ACTUATION_OBSERVED",
        {
            "subject_sha": evidence["subject_sha"],
            "intent_digest": evidence["intent_digest"],
            "exit_code": evidence["exit_code"],
            "changed": evidence["changed"],
            "observed_at": evidence["observed_at"],
        },
        first["event_digest"],
    )
    third = evidence_event(
        "POSTCONDITION_VERIFIED",
        {
            "verifier": evidence["verifier"],
            "verifier_receipt": evidence["verifier_receipt"],
            "verified": evidence["verified"],
            "postcondition_verified": True,
        },
        second["event_digest"],
    )
    fourth = evidence_event(
        "REPLAY_BOUND",
        {
            "replay": evidence["replay"],
            "reactuation_allowed": False,
        },
        third["event_digest"],
    )
    events = [first, second, third, fourth]

    result: dict[str, Any] = {
        "schema": "urn:chatman:dfcm:execution-closure:v1",
        "standing": "PARTIAL_ALIVE",
        "promotion_eligible": True,
        "alive_asserted": False,
        "subject_sha": evidence["subject_sha"],
        "intent_digest": evidence["intent_digest"],
        "authority_id": admission.get("authority_id"),
        "verifier_receipt": evidence["verifier_receipt"],
        "events": events,
        "replay": replay_evidence(events),
        "next_transition": "OWNING_MANIFEST_STANDING_ADMISSION",
        "consequential_do_performed_by_controller": False,
    }
    result["closure_digest"] = digest(result)
    return result


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic DfCM autonomic release finisher")
    parser.add_argument(
        "--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml")
    )
    parser.add_argument("--limit", type=int, default=1)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--definition-of-done",
        action="store_true",
        help="Print executable Definition of Done; exit 0 when done, 3 otherwise.",
    )
    modes.add_argument(
        "--execution-capsule",
        action="store_true",
        help="Preserve the full DfCM topology and construct an execution capsule without DO.",
    )
    modes.add_argument(
        "--admit-grant",
        type=Path,
        metavar="GRANT_JSON",
        help="Admit a BRCE grant against --capsule at deterministic --now.",
    )
    modes.add_argument(
        "--close-execution",
        type=Path,
        metavar="EVIDENCE_JSON",
        help="Bind observed execution against --capsule and --admission; never actuates.",
    )
    modes.add_argument(
        "--replay-events",
        type=Path,
        metavar="EVENTS_JSON",
        help="Verify a post-AGI DfCM evidence-event chain without reactuation.",
    )
    parser.add_argument("--capsule", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--now")
    args = parser.parse_args(argv)

    try:
        if args.definition_of_done:
            result = definition_of_done(load_manifest(args.manifest))
            emit(result)
            return 0 if result["done"] else 3
        if args.execution_capsule:
            emit(construct_capsule(load_manifest(args.manifest), args.limit))
            return 0
        if args.admit_grant is not None:
            if args.capsule is None or args.now is None:
                raise Refusal("DO_ADMISSION_INPUT_MISSING", "--capsule and --now are required")
            emit(admit_grant(load_json(args.capsule), load_json(args.admit_grant), now=args.now))
            return 0
        if args.close_execution is not None:
            if args.capsule is None or args.admission is None:
                raise Refusal(
                    "EXECUTION_CLOSURE_INPUT_MISSING",
                    "--capsule and --admission are required",
                )
            emit(
                close_execution(
                    load_json(args.capsule),
                    load_json(args.admission),
                    load_json(args.close_execution),
                )
            )
            return 0
        if args.replay_events is not None:
            events = load_json(args.replay_events)
            if not isinstance(events, list):
                raise Refusal("EVIDENCE_EVENTS_INVALID", "expected JSON array")
            emit({"replay": replay_evidence(events)})
            return 0
        emit(cycle(load_manifest(args.manifest), args.limit))
        return 0
    except (Refusal, OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        if isinstance(exc, Refusal):
            emit({"standing": "REFUSED", "code": exc.code, "detail": exc.detail})
            return 2
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
