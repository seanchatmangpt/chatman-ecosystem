"""Release closure court: every required subject has an exact SHA and a terminal disposition.

Opt-in evidence profile ``durable/v1`` (top-level ``"evidence_profile": "durable/v1"`` plus an
``evidence_root``): every court that reports ``PASS`` must bind durable evidence, and the
court recomputes it. Per court:

* ``evidence_locator`` is a CE23-9 durable locator (``git:<owner/repo>@<40hex>:<path>`` |
  ``git-notes:refs/notes/<ref>@<40hex>`` | ``https://``), else ``EVIDENCE_NOT_DURABLE``; a
  ``git:`` locator resolves ONLY at ``<root>/<owner>/<repo>/<sha>/<path>`` (the layout a
  ``git archive <sha>`` materializer writes, so the bytes are bound to the locator's
  repository and commit; no repository/SHA-blind fallback), unresolvable bytes are
  ``EVIDENCE_NOT_DURABLE:unresolved``;
* a PASS whose digest cannot be recomputed offline (an ``https://`` or ``git-notes:``
  evidence locator, or such a ``log_locator`` / ``output_locator`` backing a recorded
  ``log_sha256`` / ``output_sha256``) is ``EVIDENCE_NOT_DURABLE:unrecomputable``;
* ``evidence_digest`` recomputes over those bytes, and ``log_sha256`` / ``output_sha256``
  recompute over ``log_locator`` / ``output_locator``, else ``EVIDENCE_DIGEST_MISMATCH``;
* ``evidence_subject_sha`` (when present) is an exact commit (``EVIDENCE_SUBJECT_MUTABLE``),
  is not the container commit of its own evidence (``EVIDENCE_CONTAINER_CLAIMS_SUBJECT``;
  no field of the judged row can exempt it: a closure cannot name its own commit, so
  in-tree derivation is never verifiable here),
  and when it differs from the court ``sha`` carries ``lineage_proof{status, delta_paths,
  delta_class}`` (``EVIDENCE_LINEAGE_MISSING``, ``EVIDENCE_SUBJECT_SPLIT``); the claimed
  class must equal ``classify_delta`` (``EVIDENCE_DELTA_MISCLAIMED``), and a PASS across an
  UNBOUNDED delta is misclaimed too. A non-PASS court across an UNBOUNDED delta is reported
  in ``remaining`` as ``EVIDENCE_DELTA_UNBOUNDED``.

Without the profile the verdict is byte-identical to the tag-time court (the v26.9.25 tagged
``closure.json`` verdict is pinned by a test).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.release_train.cross_product_court.model import canonical_digest

SCHEMA = "https://chatman.dev/release-closure-court/receipt/v1"

_SHA40 = re.compile(r"^[0-9a-f]{40}$")

SPEC_STANDINGS = frozenset(
    {"FINAL_SPEC", "MERGED", "SUPERSEDED", "REFUSED", "UNSUPPORTED", "BLOCKED", "NOT_A_SPEC"}
)
IMPL_TERMINAL = frozenset(
    {
        "ALIVE",
        "PARTIAL_ALIVE",
        "PLANNED",
        "NOT_CLAIMED",
        "BLOCKED",
        "REFUSED",
        "UNSUPPORTED",
        "SUPERSEDED",
    }
)
COURT_RESULTS = frozenset({"PASS", "FAIL", "BASELINE_BLOCKER", "BLOCKED"})
AUTHORITY_RANK = {"NONE": 0, "SELECT": 1, "CONSTRUCT": 2, "DO": 3}
LINEAGE_STATES = frozenset({"OPEN", "MERGED", "CLOSED_UNMERGED"})
LINEAGE_DISPOSITIONS = frozenset({"CANONICAL", "SUPERSEDED", "UNRESOLVED", "ZOMBIE", "CLOSED"})
_NON_TERMINAL = {"BLOCKED", "UNSUPPORTED", "REFUSED"}

BASE_RULES = (
    "REFUSED:MALFORMED_ROW",
    "REFUSED:DUPLICATE_SUBJECT_ID",
    "REFUSED:MISSING_EXACT_SHA",
    "REFUSED:UNKNOWN_REQUIRED_SUBJECT",
    "REFUSED:SUPERSEDED_WITHOUT_SUCCESSOR",
    "REFUSED:SUCCESSOR_UNBOUND",
    "REFUSED:FINAL_SPEC_AS_IMPLEMENTATION_EVIDENCE",
    "REFUSED:REQUIRED_COURT_FAILED",
    "REFUSED:COURT_SUBJECT_SPLIT",
    "REFUSED:AUTHORITY_ESCALATION",
    "REFUSED:TRANSIENT_PIN",
    "REFUSED:DUPLICATE_CANONICAL_OWNER",
    "REFUSED:BLOCKED_WITHOUT_TYPE",
)
# Evidence profile durable/v1 (opt-in).
DURABLE_RULES = (
    "REFUSED:EVIDENCE_PROFILE_UNKNOWN",
    "REFUSED:EVIDENCE_NOT_DURABLE",
    "REFUSED:EVIDENCE_DIGEST_MISMATCH",
    "REFUSED:EVIDENCE_SUBJECT_MUTABLE",
    "REFUSED:EVIDENCE_SUBJECT_SPLIT",
    "REFUSED:EVIDENCE_LINEAGE_MISSING",
    "REFUSED:EVIDENCE_CONTAINER_CLAIMS_SUBJECT",
    "REFUSED:EVIDENCE_DELTA_MISCLAIMED",
)
# Lineage laws (opt-in: row ``lineage`` / ``depends_on``, closure ``max_canonical_additions``):
# exactly one admitted head per subject, no open alternative realities.
LINEAGE_RULES = (
    "REFUSED:SUCCESSOR_AMBIGUOUS",
    "REFUSED:CANONICAL_SUBJECT_SPLIT",
    "REFUSED:SUPERSEDED_LINEAGE_OPEN",
    "REFUSED:ALIVE_ON_NON_FINAL_HEAD",
    "REFUSED:SCOPE_EXCEEDS_BOUND",
    "REFUSED:DEPENDENCY_NOT_ADMITTED",
    "REFUSED:DEPENDENCY_CYCLE",
)
RULES = BASE_RULES + DURABLE_RULES + LINEAGE_RULES
EVIDENCE_PROFILES = ("durable/v1",)
_GIT_LOCATOR = re.compile(r"^git:(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40}):(?P<path>\S+)$")


@dataclass(frozen=True, slots=True)
class Verdict:
    standing: str
    refusals: tuple[str, ...]
    remaining: tuple[str, ...]
    receipt: dict[str, Any]


def _row_refusals(row: dict[str, Any]) -> list[str]:
    sid = row.get("subject_id", "?")
    out: list[str] = []
    for key in ("subject_id", "repository", "artifact", "spec_standing", "impl_standing"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:{key}")
    if out:
        return out
    if not _SHA40.fullmatch(str(row.get("sha", ""))):
        out.append(f"REFUSED:MISSING_EXACT_SHA:{sid}")
    spec, impl = row["spec_standing"], row["impl_standing"]
    required = bool(row.get("required", True))
    if spec not in SPEC_STANDINGS:
        out.append(f"REFUSED:UNKNOWN_REQUIRED_SUBJECT:{sid}:spec={spec}")
    if impl not in IMPL_TERMINAL and required:
        out.append(f"REFUSED:UNKNOWN_REQUIRED_SUBJECT:{sid}:impl={impl}")
    for label, value in (("spec", spec), ("impl", impl)):
        if value in {"BLOCKED", "REFUSED", "UNSUPPORTED"} and not str(
            row.get(f"{label}_type", "")
        ).strip():
            out.append(f"REFUSED:BLOCKED_WITHOUT_TYPE:{sid}:{label}")
    if spec == "SUPERSEDED" or impl == "SUPERSEDED":
        succ = row.get("successor")
        if not isinstance(succ, dict):
            out.append(f"REFUSED:SUPERSEDED_WITHOUT_SUCCESSOR:{sid}")
        elif not _SHA40.fullmatch(str(succ.get("sha", ""))) or not succ.get("repository"):
            out.append(f"REFUSED:SUCCESSOR_UNBOUND:{sid}")
    courts = row.get("courts", [])
    passing_impl = [
        c
        for c in courts
        if c.get("result") == "PASS" and c.get("kind", "implementation") == "implementation"
    ]
    if impl in {"ALIVE", "PARTIAL_ALIVE"} and not passing_impl:
        out.append(f"REFUSED:FINAL_SPEC_AS_IMPLEMENTATION_EVIDENCE:{sid}")
    for court in courts:
        name = court.get("court", "?")
        if court.get("result") not in COURT_RESULTS:
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:court={name}")
        elif court.get("result") == "FAIL" and court.get("required", True):
            out.append(f"REFUSED:REQUIRED_COURT_FAILED:{sid}:{name}")
        if court.get("sha") != row.get("sha"):
            out.append(f"REFUSED:COURT_SUBJECT_SPLIT:{sid}:{name}")
    ceiling = row.get("authority_ceiling", "NONE")
    claimed = row.get("authority_claimed", "NONE")
    if AUTHORITY_RANK.get(claimed, 99) > AUTHORITY_RANK.get(ceiling, -1):
        out.append(f"REFUSED:AUTHORITY_ESCALATION:{sid}:{claimed}>{ceiling}")
    return out


def _lineage_refusals(row: dict[str, Any], bound: int | None) -> list[str]:
    """PR lineage of a row: one CANONICAL head at the row sha, no open alternatives.

    Each entry: {pr, sha, state, draft, mergeable, disposition, additions?}. A row
    without ``lineage`` is unaffected.
    """
    sid = row.get("subject_id", "?")
    lineage = row.get("lineage")
    if lineage is None:
        return []
    if not isinstance(lineage, list):
        return [f"REFUSED:MALFORMED_ROW:{sid}:lineage"]
    out: list[str] = []
    canonical = []
    for pos, pr in enumerate(lineage):
        if (
            not isinstance(pr, dict)
            or not isinstance(pr.get("pr"), int)
            or isinstance(pr.get("pr"), bool)
            or not _SHA40.fullmatch(str(pr.get("sha", "")))
            or pr.get("state") not in LINEAGE_STATES
            or pr.get("disposition") not in LINEAGE_DISPOSITIONS
        ):
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:lineage[{pos}]")
            continue
        n = pr["pr"]
        if pr["disposition"] == "CANONICAL":
            canonical.append(pr)
            if pr["sha"] != row.get("sha"):
                out.append(f"REFUSED:CANONICAL_SUBJECT_SPLIT:{sid}:pr={n}")
            additions = pr.get("additions", 0)
            if bound is not None and isinstance(additions, int) and additions > bound:
                out.append(f"REFUSED:SCOPE_EXCEEDS_BOUND:{sid}:pr={n}:additions={additions}>{bound}")
        elif pr["state"] == "OPEN":
            if pr["disposition"] in {"SUPERSEDED", "ZOMBIE"}:
                out.append(f"REFUSED:SUPERSEDED_LINEAGE_OPEN:{sid}:pr={n}")
            else:
                out.append(f"REFUSED:SUCCESSOR_AMBIGUOUS:{sid}:pr={n}")
    if len(canonical) > 1:
        out.append(f"REFUSED:SUCCESSOR_AMBIGUOUS:{sid}:canonical={len(canonical)}")
    if row.get("impl_standing") == "ALIVE":
        for pr in canonical:
            if pr["state"] != "MERGED":
                out.append(
                    f"REFUSED:ALIVE_ON_NON_FINAL_HEAD:{sid}:pr={pr['pr']}:state={pr['state']}"
                    f":draft={bool(pr.get('draft'))}:mergeable={pr.get('mergeable', 'UNKNOWN')}"
                )
    return out


def _dependency_refusals(rows: list[dict[str, Any]]) -> list[str]:
    ids = {r.get("subject_id") for r in rows}
    out: list[str] = []
    graph: dict[str, list[str]] = {}
    for row in rows:
        sid = row.get("subject_id")
        deps = row.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            out.append(f"REFUSED:MALFORMED_ROW:{sid}:depends_on")
            continue
        for dep in deps:
            if dep not in ids or dep == sid:
                out.append(f"REFUSED:DEPENDENCY_NOT_ADMITTED:{sid}:{dep}")
        graph[sid] = [d for d in deps if d in ids and d != sid]
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        state[node] = 1
        for dep in graph.get(node, []):
            if state.get(dep) == 1:
                out.append(f"REFUSED:DEPENDENCY_CYCLE:{node}->{dep}")
            elif dep not in state:
                visit(dep)
        state[node] = 2

    for node in sorted(graph, key=str):
        if node not in state:
            visit(node)
    return out


def repair_order(rows: list[dict[str, Any]], remaining_ids: set[str]) -> list[str]:
    """Rows that still carry a typed blocker, dependencies first.

    Ties break by criticality: the subject that more rows (transitively) depend on
    is repaired first, then by subject_id.
    """
    graph: dict[str, list[str]] = {}
    for r in rows:
        deps = r.get("depends_on", [])
        graph[r.get("subject_id")] = [d for d in deps if isinstance(d, str)] if isinstance(deps, list) else []
    dependents: dict[str, set[str]] = {}
    for sid, deps in graph.items():
        for dep in deps:
            dependents.setdefault(dep, set()).add(sid)

    def reach(sid: str) -> int:
        seen: set[str] = set()
        stack = list(dependents.get(sid, ()))
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(dependents.get(node, ()))
        return len(seen)

    weight = {sid: reach(sid) for sid in remaining_ids}
    order: list[str] = []
    done: set[str] = set()
    while len(done) < len(remaining_ids):
        ready = [
            sid
            for sid in remaining_ids
            if sid not in done and all(d in done or d not in remaining_ids for d in graph.get(sid, []))
        ]
        if not ready:  # a cycle is refused elsewhere; emit the rest deterministically
            ready = [sid for sid in remaining_ids if sid not in done]
        nxt = min(ready, key=lambda sid: (-weight[sid], str(sid)))
        order.append(nxt)
        done.add(nxt)
    return order


def _resolve(locator: str, evidence_root: Path | None) -> bytes | None:
    match = _GIT_LOCATOR.fullmatch(locator)
    if match is None or evidence_root is None:
        return None
    path = match["path"]
    if path.startswith("/") or ".." in path.split("/"):
        return None
    if any(part in {".", ".."} for part in match["repo"].split("/")):
        return None
    # Only the (repository, commit)-addressed layout binds bytes to the locator's identity.
    candidate = evidence_root / match["repo"] / match["sha"] / path
    if candidate.is_file() and candidate.resolve().is_relative_to(evidence_root.resolve()):
        return candidate.read_bytes()
    return None


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _norm(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value if value.startswith("sha256:") else f"sha256:{value}"


def durable_refusals(
    row: dict[str, Any], evidence_root: Path | None, allowlist: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """(refusals, remaining) of one row's courts under evidence profile durable/v1."""
    from scripts.release_train.root_crown import binding

    sid = row.get("subject_id", "?")
    refusals: list[str] = []
    remaining: list[str] = []
    for court in row.get("courts", []):
        name = court.get("court", "?")
        where = f"{sid}:{name}"
        passed = court.get("result") == "PASS"
        locator = court.get("evidence_locator")
        container_sha = None
        if passed or locator is not None:
            if not binding.is_durable(locator):
                refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:{locator or court.get('evidence')}")
                continue
            match = _GIT_LOCATOR.fullmatch(locator)
            container_sha = match["sha"] if match else None
            if match is None and passed:
                refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:unrecomputable:{locator}")
                continue
            if match is not None:
                raw = _resolve(locator, evidence_root)
                if raw is None:
                    refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:unresolved:{locator}")
                    continue
                if _norm(court.get("evidence_digest")) != _sha256(raw):
                    refusals.append(f"REFUSED:EVIDENCE_DIGEST_MISMATCH:{where}:evidence")
            for field, loc_field in (("log_sha256", "log_locator"), ("output_sha256", "output_locator")):
                if court.get(field) is None:
                    continue
                companion = court.get(loc_field)
                if not binding.is_durable(companion):
                    refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:{loc_field}")
                    continue
                if not companion.startswith("git:"):
                    if passed:
                        refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:unrecomputable:{companion}")
                    continue
                raw = _resolve(companion, evidence_root)
                if raw is None:
                    refusals.append(f"REFUSED:EVIDENCE_NOT_DURABLE:{where}:unresolved:{companion}")
                elif _norm(court.get(field)) != _sha256(raw):
                    refusals.append(f"REFUSED:EVIDENCE_DIGEST_MISMATCH:{where}:{field}")
        subject = court.get("evidence_subject_sha")
        if subject is None:
            continue
        if not _SHA40.fullmatch(str(subject)):
            refusals.append(f"REFUSED:EVIDENCE_SUBJECT_MUTABLE:{where}:{subject}")
            continue
        if container_sha is not None and subject == container_sha:
            refusals.append(f"REFUSED:EVIDENCE_CONTAINER_CLAIMS_SUBJECT:{where}:{subject}")
            continue
        if subject == court.get("sha"):
            continue
        proof = court.get("lineage_proof")
        if not isinstance(proof, dict):
            refusals.append(f"REFUSED:EVIDENCE_LINEAGE_MISSING:{where}:{subject}..{court.get('sha')}")
            continue
        if proof.get("status") in binding.LINEAGE_BAD:
            refusals.append(f"REFUSED:EVIDENCE_SUBJECT_SPLIT:{where}:{proof.get('status')}")
            continue
        if proof.get("status") not in binding.LINEAGE_OK or not isinstance(proof.get("delta_paths"), list):
            refusals.append(f"REFUSED:EVIDENCE_LINEAGE_MISSING:{where}:status={proof.get('status')}")
            continue
        computed, _ = binding.classify_delta(proof["delta_paths"], allowlist)
        if proof.get("delta_class") != computed:
            refusals.append(f"REFUSED:EVIDENCE_DELTA_MISCLAIMED:{where}:claimed={proof.get('delta_class')}:computed={computed}")
        elif computed == "UNBOUNDED":
            if passed:
                refusals.append(f"REFUSED:EVIDENCE_DELTA_MISCLAIMED:{where}:PASS-across-UNBOUNDED")
            else:
                remaining.append(f"{sid}:court:{name}:EVIDENCE_DELTA_UNBOUNDED")
    return refusals, remaining


def bind_index(
    closure: dict[str, Any], index: dict[str, Any], deltas: dict[str, Any] | None = None
) -> dict[str, Any]:
    """A durable/v1 copy of ``closure`` whose courts bind the E1 evidence index rows.

    ``index`` is ``hardening/evidence/INDEX.json`` (scripts/durable_locator): each row names
    the court (``closure_pointer`` ``/subjects/<i>/courts/<j>/evidence``), its durable locator
    and sha256, and companions whose ``recorded_field`` (``log_sha256``/``output_sha256``)
    names the closure digest they back. ``deltas`` (``hardening/inputs/delta-observations.json``)
    supplies the ``lineage_proof`` of each court whose ``evidence_subject_sha`` differs from its
    ``sha``, classified against the release allowlist. Courts without a row are left as they are.
    """
    from scripts.release_train.root_crown import binding

    out = json.loads(json.dumps(closure))
    out["evidence_profile"] = "durable/v1"
    try:
        allowlist = binding.load_allowlist(str(closure.get("release")))
    except (OSError, json.JSONDecodeError):
        allowlist = {}
    observed = {
        (p.get("repository"), p.get("base"), p.get("head")): p for p in (deltas or {}).get("pairs", [])
    }
    for row in out.get("subjects", []):
        for court in row.get("courts", []):
            pair = observed.get((row.get("repository"), court.get("evidence_subject_sha"), court.get("sha")))
            if pair is not None and court.get("evidence_subject_sha") != court.get("sha"):
                computed, _ = binding.classify_delta(pair.get("delta_paths"), allowlist)
                court["lineage_proof"] = {
                    "status": pair.get("status"),
                    "delta_paths": pair.get("delta_paths"),
                    "delta_class": computed,
                }
    for row in index.get("rows", []):
        parts = str(row.get("closure_pointer", "")).strip("/").split("/")
        if len(parts) != 5 or parts[0] != "subjects" or parts[2] != "courts" or parts[4] != "evidence":
            continue
        court = out["subjects"][int(parts[1])]["courts"][int(parts[3])]
        court["evidence_locator"] = row["durable_locator"]
        court["evidence_digest"] = "sha256:" + str(row["sha256"])
        for companion in row.get("companions", []):
            field = companion.get("recorded_field")
            if field in ("log_sha256", "output_sha256"):
                court[field.replace("_sha256", "_locator")] = companion["durable_locator"]
    return out


def evaluate(closure: dict[str, Any], evidence_root: Path | None = None) -> Verdict:
    """Closure verdict. ``evidence_root`` is read only under ``evidence_profile: durable/v1``."""
    rows = closure.get("subjects", [])
    refusals: list[str] = []
    profile = closure.get("evidence_profile")
    durable_remaining: list[str] = []
    if profile is not None:
        if profile not in EVIDENCE_PROFILES:
            refusals.append(f"REFUSED:EVIDENCE_PROFILE_UNKNOWN:{profile}")
        else:
            from scripts.release_train.root_crown import binding

            try:
                allowlist = binding.load_allowlist(str(closure.get("release")))
            except (OSError, json.JSONDecodeError):
                allowlist = {}
            for row in rows:
                found, rest = durable_refusals(row, evidence_root, allowlist)
                refusals.extend(found)
                durable_remaining.extend(rest)
    if not rows:
        refusals.append("REFUSED:MALFORMED_ROW:closure:subjects-empty")
    ids = [r.get("subject_id") for r in rows]
    for dup in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        refusals.append(f"REFUSED:DUPLICATE_SUBJECT_ID:{dup}")
    bound = closure.get("max_canonical_additions")
    if bound is not None and (not isinstance(bound, int) or isinstance(bound, bool) or bound < 0):
        refusals.append("REFUSED:MALFORMED_ROW:closure:max_canonical_additions")
        bound = None
    for row in rows:
        refusals.extend(_row_refusals(row))
        refusals.extend(_lineage_refusals(row, bound))
    refusals.extend(_dependency_refusals(rows))

    transient = {t["sha"]: t for t in closure.get("transient_heads", [])}
    for row in rows:
        for pin in row.get("pins", []):
            hit = transient.get(pin.get("sha"))
            if hit is not None:
                refusals.append(
                    f"REFUSED:TRANSIENT_PIN:{row.get('subject_id')}:{pin.get('sha')}"
                    f"->durable={hit.get('replaced_by')}"
                )

    owners: dict[str, set[tuple[str, str]]] = {}
    for row in rows:
        rfc = row.get("rfc_id")
        if rfc and row.get("spec_standing") == "FINAL_SPEC":
            owners.setdefault(rfc, set()).add((row.get("repository"), row.get("artifact")))
    for rfc, where in sorted(owners.items()):
        if len(where) > 1:
            refusals.append(f"REFUSED:DUPLICATE_CANONICAL_OWNER:{rfc}")

    remaining = tuple(
        sorted(
            f"{r.get('subject_id')}:{label}:{r.get(label + '_standing')}"
            f"({r.get(label + '_type', '')})"
            for r in rows
            for label in ("spec", "impl")
            if r.get(label + "_standing") in {"BLOCKED", "UNSUPPORTED", "REFUSED"}
        )
        + sorted(durable_remaining)
    )
    refusals = sorted(set(refusals))
    if refusals:
        standing = "REFUSED"
    elif remaining:
        standing = "PARTIAL_ALIVE"
    else:
        standing = "ALIVE"
    payload = {
        "schema": SCHEMA,
        "release": closure.get("release"),
        "normative_ledger": closure.get("normative_ledger"),
        "standing": standing,
        "refusals": refusals,
        "remaining": list(remaining),
        "subjects": sorted(
            f"{r.get('subject_id')}={r.get('repository')}@{r.get('sha')}" for r in rows
        ),
        "authority": "NONE",
    }
    if any("depends_on" in r for r in rows):
        # Present only when the closure declares edges, so existing receipts keep their digest.
        payload["repair_order"] = repair_order(rows, {
            r.get("subject_id")
            for r in rows
            if r.get("spec_standing") in _NON_TERMINAL or r.get("impl_standing") in _NON_TERMINAL
        })
    if profile is not None:
        payload["evidence_profile"] = profile
    payload["receipt_digest"] = canonical_digest(payload)
    return Verdict(standing, tuple(refusals), remaining, payload)


def evaluate_path(path: str | Path, evidence_root: str | Path | None = None) -> Verdict:
    return evaluate(
        json.loads(Path(path).read_text(encoding="utf-8")),
        None if evidence_root is None else Path(evidence_root),
    )
