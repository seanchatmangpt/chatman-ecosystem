"""Ecosystem closure compiler (v26.9.24).

Compiles one machine-readable closure manifest into one closure receipt and
refuses the crown unless, for every required subject r,

    exists-unique SHA_r  and FINAL(r)  and V(SHA_r) = PASS
    and Dep(r) is contained in E_admitted  and R_r replayable

The compiler is a pure function of the manifest bytes: it performs no network,
subprocess, or filesystem mutation. Live observation (ls-remote, PR state, CI
conclusions) is recorded *into* the manifest by an observer and is data here.

Standing vocabulary follows AGENTS.md. A subject is ALIVE only with zero
findings; the closure is ALIVE only when every required subject is ALIVE and
no closure-level finding exists. UNKNOWN is never ALIVE.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

SCHEMA = "https://chatman.dev/ecosystem-closure/receipt/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

STANDINGS = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}
PR_STATES = {"OPEN", "MERGED", "CLOSED_UNMERGED"}
MERGEABILITY = {"MERGEABLE", "CONFLICTING", "UNKNOWN"}
DISPOSITIONS = {"CANONICAL", "SUPERSEDED", "UNRESOLVED", "ZOMBIE", "EXTRACT", "CLOSED"}
SUBJECT_SOURCES = {"canonical-pr", "default-head", "unresolved"}
CONCLUSIONS = {"SUCCESS", "FAILURE", "CANCELLED", "IN_PROGRESS", "NONE", "UNKNOWN"}
TRUTH = {"PASS", "FAIL", "UNKNOWN"}
CLASSES = {"SPINE", "MANUFACTURE", "PROVE_OBSERVE", "EXPLORE", "APPLICATION"}


class ClosureMalformed(ValueError):
    """The manifest is not a closure manifest; str(error) starts with its code."""


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    subject: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "subject": self.subject, "detail": self.detail}


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _need(table: dict[str, Any], key: str, kind: type | tuple[type, ...], where: str) -> Any:
    if key not in table:
        raise ClosureMalformed(f"CLOSURE_FIELD_MISSING:{where}.{key}")
    value = table[key]
    # bool is an int subclass; refuse it where an int is required.
    if kind is int and isinstance(value, bool):
        raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{where}.{key}")
    if not isinstance(value, kind):
        raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{where}.{key}")
    return value


def _enum(value: Any, allowed: set[str], where: str) -> str:
    if value not in allowed:
        raise ClosureMalformed(f"CLOSURE_ENUM_INVALID:{where}={value}")
    return value


def validate_shape(data: dict[str, Any]) -> None:
    """Raise ClosureMalformed unless ``data`` has the closure manifest shape."""
    closure = data.get("closure")
    if not isinstance(closure, dict):
        raise ClosureMalformed("CLOSURE_SECTION_MISSING:closure")
    _need(closure, "version", str, "closure")
    _need(closure, "observed_at", str, "closure")
    _need(closure, "root_repository", str, "closure")
    _enum(_need(closure, "standing", str, "closure"), STANDINGS, "closure.standing")
    spine = _need(closure, "spine", list, "closure")
    if not spine or not all(isinstance(item, str) for item in spine):
        raise ClosureMalformed("CLOSURE_FIELD_TYPE:closure.spine")
    _need(closure, "max_canonical_additions", int, "closure")

    subjects = data.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        raise ClosureMalformed("CLOSURE_SUBJECTS_MISSING:subjects")
    for index, subject in enumerate(subjects):
        where = f"subjects[{index}]"
        if not isinstance(subject, dict):
            raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{where}")
        where = f"subjects.{subject.get('id', index)}"
        _need(subject, "id", str, where)
        _need(subject, "repository", str, where)
        _need(subject, "role", str, where)
        _enum(_need(subject, "class", str, where), CLASSES, f"{where}.class")
        _need(subject, "required", bool, where)
        _need(subject, "normative", bool, where)
        _enum(_need(subject, "standing", str, where), STANDINGS, f"{where}.standing")
        _need(subject, "sha", str, where)
        _enum(_need(subject, "subject_source", str, where), SUBJECT_SOURCES, f"{where}.subject_source")
        _need(subject, "default_head", str, where)
        deps = _need(subject, "depends_on", list, where)
        if not all(isinstance(dep, str) for dep in deps):
            raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{where}.depends_on")
        pins = subject.get("dependency_shas", {})
        if not isinstance(pins, dict) or not all(isinstance(v, str) for v in pins.values()):
            raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{where}.dependency_shas")
        _need(subject, "terminal_disposition", str, where)
        _need(subject, "unenumerated_open_lineage", int, where)

        for pos, pr in enumerate(_need(subject, "lineage", list, where)):
            pwhere = f"{where}.lineage[{pos}]"
            if not isinstance(pr, dict):
                raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{pwhere}")
            _need(pr, "pr", int, pwhere)
            _need(pr, "sha", str, pwhere)
            _enum(_need(pr, "state", str, pwhere), PR_STATES, f"{pwhere}.state")
            _need(pr, "draft", bool, pwhere)
            _enum(_need(pr, "mergeable", str, pwhere), MERGEABILITY, f"{pwhere}.mergeable")
            _enum(_need(pr, "disposition", str, pwhere), DISPOSITIONS, f"{pwhere}.disposition")
            _need(pr, "additions", int, pwhere)

        verifier = _need(subject, "verifier", dict, where)
        _need(verifier, "court", str, f"{where}.verifier")
        _enum(_need(verifier, "conclusion", str, f"{where}.verifier"), CONCLUSIONS, f"{where}.verifier.conclusion")
        _need(verifier, "run_head_sha", str, f"{where}.verifier")

        receipt = _need(subject, "receipt", dict, where)
        _need(receipt, "digest", str, f"{where}.receipt")
        _enum(_need(receipt, "replay", str, f"{where}.receipt"), TRUTH, f"{where}.receipt.replay")

        propositions = _need(subject, "propositions", list, where)
        for pos, prop in enumerate(propositions):
            qwhere = f"{where}.propositions[{pos}]"
            if not isinstance(prop, dict):
                raise ClosureMalformed(f"CLOSURE_FIELD_TYPE:{qwhere}")
            _need(prop, "id", str, qwhere)
            _enum(_need(prop, "state", str, qwhere), TRUTH, f"{qwhere}.state")


def _subject_findings(subject: dict[str, Any], by_id: dict[str, dict[str, Any]], bound: int) -> list[Finding]:
    sid = subject["id"]
    out: list[Finding] = []

    def f(code: str, detail: str) -> None:
        out.append(Finding(code, sid, detail))

    sha = subject["sha"]
    if not REPO.fullmatch(subject["repository"]):
        f("CLOSURE_REPOSITORY_INVALID", subject["repository"])
    if subject["subject_source"] == "unresolved" or not SHA40.fullmatch(sha):
        f("CLOSURE_SUBJECT_UNRESOLVED", f"sha={sha}")

    # Lineage: exists-unique successor.
    lineage = subject["lineage"]
    canonical = [pr for pr in lineage if pr["disposition"] == "CANONICAL"]
    if subject["subject_source"] == "canonical-pr":
        if len(canonical) != 1:
            f("CLOSURE_CANONICAL_PR_AMBIGUOUS", f"canonical_count={len(canonical)}")
        elif canonical[0]["sha"] != sha:
            f("CLOSURE_CANONICAL_SUBJECT_SPLIT", f"pr={canonical[0]['pr']}:pr_sha={canonical[0]['sha']}:subject={sha}")
    elif subject["subject_source"] == "default-head":
        if canonical:
            f("CLOSURE_CANONICAL_PR_AMBIGUOUS", "default-head subject also names a CANONICAL pr")
        if sha != subject["default_head"]:
            f("CLOSURE_DEFAULT_HEAD_SPLIT", f"default_head={subject['default_head']}:subject={sha}")
        f("CLOSURE_CANONICAL_BINDING_ABSENT", "subject bound to an observed default head with no canonical release PR")

    for pr in canonical:
        n = pr["pr"]
        if pr["state"] == "CLOSED_UNMERGED":
            f("CLOSURE_CANONICAL_PR_CLOSED", f"pr={n}")
        if pr["state"] == "OPEN":
            f("CLOSURE_HEAD_NOT_FINAL", f"pr={n}:state=OPEN")
            if pr["draft"]:
                f("CLOSURE_NORMATIVE_RFC_DRAFT" if subject["normative"] else "CLOSURE_HEAD_DRAFT", f"pr={n}")
            if pr["mergeable"] == "CONFLICTING":
                f("CLOSURE_HEAD_NOT_MERGEABLE", f"pr={n}")
            elif pr["mergeable"] == "UNKNOWN":
                f("CLOSURE_MERGEABILITY_UNKNOWN", f"pr={n}")
        if subject["normative"] and pr["state"] != "MERGED":
            f("CLOSURE_NORMATIVE_ROOT_NOT_ADMITTED", f"pr={n}")
        if pr["additions"] > bound:
            f("CLOSURE_SCOPE_EXCEEDS_BOUND", f"pr={n}:additions={pr['additions']}:bound={bound}")

    for pr in lineage:
        if pr["state"] != "OPEN" or pr["disposition"] == "CANONICAL":
            continue
        code = {
            "UNRESOLVED": "CLOSURE_SUCCESSOR_AMBIGUOUS",
            "ZOMBIE": "CLOSURE_ZOMBIE_LINEAGE_OPEN",
            "SUPERSEDED": "CLOSURE_SUPERSEDED_LINEAGE_OPEN",
            "EXTRACT": "CLOSURE_EXTRACTION_PENDING",
            "CLOSED": "CLOSURE_LINEAGE_STATE_SPLIT",
        }[pr["disposition"]]
        f(code, f"pr={pr['pr']}:sha={pr['sha']}")
    if subject["unenumerated_open_lineage"] > 0:
        f("CLOSURE_LINEAGE_UNENUMERATED", f"open_unenumerated={subject['unenumerated_open_lineage']}")

    # Verification at the exact head.
    verifier = subject["verifier"]
    conclusion = verifier["conclusion"]
    if conclusion != "SUCCESS":
        f("CLOSURE_VERIFICATION_NOT_GREEN", f"court={verifier['court']}:conclusion={conclusion}")
    elif verifier["run_head_sha"] != sha:
        f("CLOSURE_VERIFICATION_SUBJECT_SPLIT", f"court={verifier['court']}:run_head={verifier['run_head_sha']}:subject={sha}")

    for prop in subject["propositions"]:
        if prop["state"] == "UNKNOWN":
            f("CLOSURE_PROPOSITION_UNKNOWN", prop["id"])
        elif prop["state"] == "FAIL":
            f("CLOSURE_PROPOSITION_FAILED", prop["id"])
    if not subject["propositions"]:
        f("CLOSURE_PROPOSITIONS_EMPTY", "a subject with no propositions proves nothing")

    receipt = subject["receipt"]
    if not SHA256.fullmatch(receipt["digest"]):
        f("CLOSURE_RECEIPT_MISSING", f"digest={receipt['digest'] or '<empty>'}")
    if receipt["replay"] != "PASS":
        f("CLOSURE_RECEIPT_NOT_REPLAYED", f"replay={receipt['replay']}")

    # Dependencies: Dep(r) contained in E_admitted, pinned by exact SHA.
    pins = subject.get("dependency_shas", {})
    for dep in subject["depends_on"]:
        target = by_id.get(dep)
        if dep == sid:
            f("CLOSURE_SELF_DEPENDENCY", dep)
        elif target is None:
            f("CLOSURE_DEPENDENCY_NOT_ADMITTED", dep)
        else:
            if subject["required"] and not target["required"]:
                f("CLOSURE_DEPENDENCY_NOT_REQUIRED", dep)
            pin = pins.get(dep)
            if pin is None:
                f("CLOSURE_DEPENDENCY_SHA_UNBOUND", dep)
            elif pin != target["sha"]:
                f("CLOSURE_DEPENDENCY_SHA_SPLIT", f"{dep}:pinned={pin}:admitted={target['sha']}")
    for dep in sorted(set(pins) - set(subject["depends_on"])):
        f("CLOSURE_DEPENDENCY_PIN_UNDECLARED", dep)
    return out


def _cycle_findings(by_id: dict[str, dict[str, Any]]) -> list[Finding]:
    state: dict[str, int] = {}
    found: list[Finding] = []

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        for dep in by_id[node]["depends_on"]:
            if dep not in by_id or dep == node:
                continue
            if state.get(dep) == 1:
                cycle = path[path.index(dep):] + [dep] if dep in path else [node, dep]
                found.append(Finding("CLOSURE_DEPENDENCY_CYCLE", dep, "->".join(cycle)))
            elif dep not in state:
                visit(dep, path + [dep])
        state[node] = 2

    for node in sorted(by_id):
        if node not in state:
            visit(node, [node])
    return found


def repair_order(subjects: list[dict[str, Any]], blocked: set[str], spine: list[str]) -> list[str]:
    """Blocked required subjects, dependencies first.

    Ties break by spine criticality: a subject ranks at the earliest spine
    position that (transitively) depends on it, so a leaf feeding the SA2A
    edge is repaired before one that only feeds the crown.
    """
    spine_pos = {sid: pos for pos, sid in enumerate(spine)}
    dependents: dict[str, set[str]] = {}
    for s in subjects:
        for d in s["depends_on"]:
            dependents.setdefault(d, set()).add(s["id"])
    rank: dict[str, int] = {}
    for s in subjects:
        seen, stack, best = set(), [s["id"]], len(spine)
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            best = min(best, spine_pos.get(node, len(spine)))
            stack.extend(dependents.get(node, ()))
        rank[s["id"]] = best
    ids = [s["id"] for s in subjects if s["id"] in blocked]
    deps = {s["id"]: [d for d in s["depends_on"] if d in blocked and d != s["id"]] for s in subjects if s["id"] in blocked}
    order: list[str] = []
    done: set[str] = set()
    key = lambda sid: (rank[sid], spine_pos.get(sid, len(spine)), sid)  # noqa: E731
    while len(done) < len(ids):
        ready = sorted((sid for sid in ids if sid not in done and all(d in done for d in deps[sid])), key=key)
        if not ready:  # cycle: emit the remainder deterministically
            order.extend(sorted((sid for sid in ids if sid not in done), key=key))
            break
        order.append(ready[0])
        done.add(ready[0])
    return order


def sid_alive(verdicts: list[dict[str, Any]], sid: str) -> bool:
    return any(v["id"] == sid and v["computed_standing"] == "ALIVE" for v in verdicts)


def compile_closure(data: dict[str, Any], manifest_digest: str) -> dict[str, Any]:
    """Compile a closure manifest into a deterministic closure receipt."""
    validate_shape(data)
    closure = data["closure"]
    subjects: list[dict[str, Any]] = data["subjects"]
    bound = closure["max_canonical_additions"]
    global_findings: list[Finding] = []

    by_id: dict[str, dict[str, Any]] = {}
    repositories: dict[str, str] = {}
    for subject in subjects:
        sid = subject["id"]
        if sid in by_id:
            global_findings.append(Finding("CLOSURE_DUPLICATE_SUBJECT_ID", sid, "subject id must be unique"))
            continue
        by_id[sid] = subject
        repo = subject["repository"]
        if repo in repositories:
            global_findings.append(Finding("CLOSURE_DUPLICATE_REPOSITORY", repo, f"{repositories[repo]} and {sid}: exactly one admitted head per repository"))
        else:
            repositories[repo] = sid

    root = closure["root_repository"]
    if root not in repositories:
        global_findings.append(Finding("CLOSURE_ROOT_NOT_ADMITTED", root, "the crown repository must be a subject"))
    elif not by_id[repositories[root]]["required"]:
        global_findings.append(Finding("CLOSURE_ROOT_NOT_REQUIRED", root, "the crown repository must be required"))

    spine = closure["spine"]
    for pos, sid in enumerate(spine):
        subject = by_id.get(sid)
        if subject is None:
            global_findings.append(Finding("CLOSURE_SPINE_SUBJECT_MISSING", sid, f"spine[{pos}]"))
            continue
        if not subject["required"]:
            global_findings.append(Finding("CLOSURE_SPINE_NOT_REQUIRED", sid, f"spine[{pos}]"))
        if pos > 0 and spine[pos - 1] not in subject["depends_on"]:
            global_findings.append(Finding("CLOSURE_SPINE_EDGE_MISSING", sid, f"must depend on {spine[pos - 1]}"))
    if len(spine) != len(set(spine)):
        global_findings.append(Finding("CLOSURE_SPINE_DUPLICATE", "closure.spine", "spine subjects must be unique"))
    if spine and repositories.get(root) != spine[-1]:
        global_findings.append(Finding("CLOSURE_SPINE_NOT_CROWNED", "closure.spine", "the spine must terminate at the crown repository"))

    global_findings.extend(_cycle_findings(by_id))

    verdicts: list[dict[str, Any]] = []
    blocked_required: set[str] = set()
    overclaims: list[Finding] = []
    for sid in sorted(by_id):
        subject = by_id[sid]
        findings = _subject_findings(subject, by_id, bound)
        computed = "ALIVE" if not findings else "BLOCKED"
        if subject["standing"] == "ALIVE" and computed != "ALIVE":
            overclaims.append(Finding("CLOSURE_STANDING_OVERCLAIM", sid, f"declared=ALIVE:computed={computed}"))
        if subject["required"] and computed != "ALIVE":
            blocked_required.add(sid)
        verdicts.append({
            "id": sid,
            "repository": subject["repository"],
            "sha": subject["sha"],
            "required": subject["required"],
            "class": subject["class"],
            "declared_standing": subject["standing"],
            "computed_standing": computed,
            "terminal_disposition": subject["terminal_disposition"],
            "findings": [item.as_dict() for item in sorted(findings, key=lambda x: (x.code, x.detail))],
        })

    closure_alive = not blocked_required and not global_findings and not overclaims
    computed = "ALIVE" if closure_alive else "BLOCKED"
    if closure["standing"] == "ALIVE" and computed != "ALIVE":
        overclaims.append(Finding("CLOSURE_STANDING_OVERCLAIM", "closure", f"declared=ALIVE:computed={computed}"))

    code_counts: dict[str, int] = {}
    for verdict in verdicts:
        if verdict["required"]:
            for item in verdict["findings"]:
                code_counts[item["code"]] = code_counts.get(item["code"], 0) + 1

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "version": closure["version"],
        "observed_at": closure["observed_at"],
        "manifest_digest": manifest_digest,
        "authority": "NONE",
        "declared_standing": closure["standing"],
        "computed_standing": computed,
        "required_subjects": sorted(sid for sid, s in by_id.items() if s["required"]),
        "admitted_subjects": sorted(f"{s['repository']}@{s['sha']}" for s in by_id.values() if s["required"] and sid_alive(verdicts, s["id"])),
        "blocked_required": sorted(blocked_required),
        "repair_order": repair_order(subjects, blocked_required, spine),
        "required_finding_counts": dict(sorted(code_counts.items())),
        "closure_findings": [item.as_dict() for item in sorted(global_findings, key=lambda x: (x.code, x.subject))],
        "overclaims": [item.as_dict() for item in sorted(overclaims, key=lambda x: x.subject)],
        "subjects": verdicts,
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    return receipt


def verify_receipt(receipt: dict[str, Any]) -> bool:
    """True when ``receipt`` carries the digest of its own canonical payload."""
    body = {k: v for k, v in receipt.items() if k != "receipt_digest"}
    return receipt.get("receipt_digest") == canonical_digest(body)
