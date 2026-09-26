"""Evidence binding: every PASS names what it evaluated and where its evidence durably lives.

An ``EvidenceBinding`` (model.py) separates two commits that the tag-time crown conflated:

* ``evaluated_subject_sha``: the commit the evidence speaks about (the producer subject);
* ``evidence_container_sha``: the commit that holds the evidence bytes (the receipt commit).

A receipt cannot contain the hash of the commit that contains it, so for any receipt the two
differ, and the container head inherits the producer's standing only through a lineage
proof: an observed compare status (``identical``/``ahead``) plus the changed paths between
them, classified by ``classify_delta`` against the committed allowlist
(``policy/<release>/delta-allowlist.json``: ``.json`` under ``release/*/receipts/`` only).

``admit`` is the admission function. Refusals (each makes the requirement REFUSED):

* ``EVIDENCE_NOT_DURABLE``: the evidence locator is not a CE23-9 durable locator
  (``git:<owner/repo>@<40hex>:<path>`` | ``git-notes:refs/notes/<ref>@<40hex>`` | ``https://``);
  absolute, scratch, tmp and ``~`` paths are never evidence.
* ``EVIDENCE_SUBJECT_MUTABLE``: the evaluated subject or the container is not an exact
  40-hex commit (a branch, a tag name, a short sha).
* ``EVIDENCE_CONTAINER_CLAIMS_SUBJECT``: a receipt names as its evaluated subject the
  crown (release container) commit, or the very commit that contains it.
* ``EVIDENCE_SUBJECT_SPLIT``: the subject is behind/diverged from the container, or an
  IN_TREE_DERIVED binding evaluated another commit than its container.
* ``EVIDENCE_LINEAGE_MISSING``: subject and container differ and no lineage proof (status
  ``ahead``/``identical`` plus delta paths) was observed.
* ``EVIDENCE_DIGEST_MISMATCH``: the evidence bytes, or the binding itself, do not recompute.
* ``EVIDENCE_DELTA_MISCLAIMED``: the claimed delta class differs from the computed one.

Typed blocker: ``EVIDENCE_DELTA_UNBOUNDED`` (EVIDENCE_FAILURE, R_missing_identity): the
delta holds non-receipt paths; the producer standing is not inherited by the container.

Pure: reads only the allowlist file; no process, no network.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import BINDING_KINDS, BLOCKED, REFUSED, EvidenceBinding, ReqState, Requirement

HEX40 = re.compile(r"^[0-9a-f]{40}$")
_REPO = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
DURABLE_LOCATOR = re.compile(
    rf"^(?:git:{_REPO}@[0-9a-f]{{40}}:(?!/)(?!.*(?:^|/)\.\.(?:/|$))\S+"
    r"|git-notes:refs/notes/[A-Za-z0-9_./-]+@[0-9a-f]{40}"
    r"|https://\S+)$"
)
ALLOWLIST_FILE = "delta-allowlist.json"
POLICY_ROOT = Path(__file__).resolve().parent / "policy"
DELTA_CLASSES = ("EMPTY", "RECEIPT_ONLY", "UNBOUNDED")
LINEAGE_OK = ("identical", "ahead")
LINEAGE_BAD = ("behind", "diverged")
# Receipt kinds: the evidence is a receipt produced about another commit.
RECEIPT_KINDS = ("REMOTE_RECEIPT", "OPERATOR_LOCAL", "LOCAL_RECEIPT")


def is_durable(locator: Any) -> bool:
    return isinstance(locator, str) and DURABLE_LOCATOR.fullmatch(locator) is not None


def git_locator(repository: str | None, sha: str | None, path: str) -> str | None:
    """``git:<repo>@<sha>:<path>``, or None when the container is not an exact commit."""
    if not repository or not isinstance(sha, str) or not HEX40.fullmatch(sha):
        return None
    return f"git:{repository}@{sha}:{path}"


def sha256_tag(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _norm_digest(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value if value.startswith("sha256:") else f"sha256:{value}"


# ------------------------------------------------------------------ delta classification


def load_allowlist(release: str, root: Path = POLICY_ROOT) -> dict[str, Any]:
    return json.loads((root / release / ALLOWLIST_FILE).read_text(encoding="utf-8"))


def _glob_rx(pattern: str) -> re.Pattern[str]:
    """``*`` = one path segment's characters, ``**`` = any characters including ``/``."""
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def path_admitted(path: Any, allowlist: dict[str, Any]) -> bool:
    """One changed path is inert: matches an allow glob, no traversal, no denied segment/extension."""
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        return False
    segments = path.split("/")
    if any(s in ("", ".", "..") for s in segments):
        return False
    lowered = path.lower()
    if any(lowered.endswith(ext) for ext in allowlist.get("deny_extensions", [])):
        return False
    if set(segments) & set(allowlist.get("deny_segments", [])):
        return False
    return any(_glob_rx(p).fullmatch(path) for p in allowlist.get("allow", []))


def classify_delta(paths: Iterable[str] | None, allowlist: dict[str, Any]) -> tuple[str | None, list[str]]:
    """(class, offending paths). None paths (unobserved) -> (None, []).

    EMPTY: no changed path. RECEIPT_ONLY: every path is an inert receipt. UNBOUNDED: any
    other path (the offending paths are returned sorted).
    """
    if paths is None:
        return None, []
    items = sorted(set(paths))
    if not items:
        return "EMPTY", []
    offending = [p for p in items if not path_admitted(p, allowlist)]
    return ("UNBOUNDED" if offending else "RECEIPT_ONLY"), offending


# ------------------------------------------------------------------ constructors


def _lineage(status: str | None, paths: Iterable[str] | None, allowlist: dict[str, Any], claimed: Any = None) -> dict[str, Any]:
    items = None if paths is None else sorted(set(paths))
    computed, _ = classify_delta(items, allowlist)
    return {"status": status, "delta_paths": items, "delta_class": claimed if claimed is not None else computed}


def bind_in_tree(
    req: Requirement,
    crown_sha: str,
    container_repository: str | None,
    path: str,
    evidence_bytes: bytes | None,
    *,
    court: str,
    standing: str = "PASS",
    derivation: str = "",
) -> EvidenceBinding:
    """IN_TREE_DERIVED: the crown derived this from its own tree at ``crown_sha``.

    The evidence digest is the digest of the file bytes at ``path`` when the evaluator read a
    file, else of the derivation record (the evaluator's own detail).
    """
    digest = sha256_tag(evidence_bytes if evidence_bytes is not None else derivation.encode("utf-8"))
    return EvidenceBinding(
        requirement_id=req.id,
        kind="IN_TREE_DERIVED",
        evaluated_subject_sha=crown_sha,
        evaluated_subject_kind="crown_commit",
        container_repository=container_repository,
        evidence_container_sha=crown_sha,
        evidence_locator=git_locator(container_repository, crown_sha, path),
        evidence_digest=digest,
        producer="root-crown",
        court=court,
        command=None,
        exit_code=None,
        toolchain=None,
        standing=standing,
        owner=container_repository,
        owner_source="container",
        lineage_proof={"status": "identical", "delta_paths": [], "delta_class": "EMPTY"},
    ).sealed()


def bind_remote(
    req: Requirement,
    *,
    repository: str | None,
    path: str,
    subject_sha: Any,
    container_sha: Any,
    evidence_digest: Any,
    compare_status: str | None,
    delta_paths: Iterable[str] | None,
    allowlist: dict[str, Any],
    data: dict[str, Any],
    standing: str | None,
    owner: str | None,
    owner_source: str,
    kind: str = "REMOTE_RECEIPT",
) -> EvidenceBinding:
    """REMOTE_RECEIPT / OPERATOR_LOCAL: a producer receipt read from ``repository`` at ``container_sha``."""
    if kind not in RECEIPT_KINDS:
        raise ValueError(f"receipt binding kind {kind!r} not in {RECEIPT_KINDS}")
    same = isinstance(subject_sha, str) and subject_sha == container_sha
    paths = [] if same and delta_paths is None else delta_paths
    claimed = data.get("subject_delta_class") or data.get("delta_class")
    return EvidenceBinding(
        requirement_id=req.id,
        kind=kind,
        evaluated_subject_sha=subject_sha if isinstance(subject_sha, str) else None,
        evaluated_subject_kind="producer_commit",
        container_repository=repository,
        evidence_container_sha=container_sha if isinstance(container_sha, str) else None,
        evidence_locator=git_locator(repository, container_sha, path),
        evidence_digest=_norm_digest(evidence_digest),
        producer=str(data.get("producer") or repository or ""),
        court=str(data.get("court") or data.get("gate") or req.evidence_kind),
        command=data.get("command") if isinstance(data.get("command"), str) else None,
        exit_code=data.get("exit_code") if isinstance(data.get("exit_code"), int) else None,
        toolchain=data.get("toolchain") if isinstance(data.get("toolchain"), str) else None,
        standing=standing,
        owner=owner,
        owner_source=owner_source,
        lineage_proof=_lineage("identical" if same else compare_status, paths, allowlist, claimed),
    ).sealed()


def bind_local(
    req: Requirement,
    crown_sha: str,
    container_repository: str | None,
    path: str,
    evidence_bytes: bytes,
    data: dict[str, Any],
    standing: str | None,
    allowlist: dict[str, Any],
    *,
    kind: str = "LOCAL_RECEIPT",
) -> EvidenceBinding:
    """LOCAL_RECEIPT / OPERATOR_LOCAL: a receipt committed in the crown tree.

    Its container is the crown commit. When the receipt names a subject of its own, that is
    the evaluated subject (and it may not be the container: a commit cannot contain its own
    hash); otherwise the receipt speaks about operator-local state observed at the container.
    """
    subject = data.get("subject_sha")
    if not subject and isinstance(data.get("subject"), dict):
        subject = data["subject"].get("sha")
    has_subject = isinstance(subject, str) and subject != ""
    return EvidenceBinding(
        requirement_id=req.id,
        kind=kind,
        evaluated_subject_sha=subject if has_subject else crown_sha,
        evaluated_subject_kind="producer_commit" if has_subject else "operator_local_state",
        container_repository=container_repository,
        evidence_container_sha=crown_sha,
        evidence_locator=git_locator(container_repository, crown_sha, path),
        evidence_digest=sha256_tag(evidence_bytes),
        producer=str(data.get("producer") or "operator-local"),
        court=str(data.get("court") or req.evidence_kind),
        command=data.get("command") if isinstance(data.get("command"), str) else None,
        exit_code=data.get("exit_code") if isinstance(data.get("exit_code"), int) else None,
        toolchain=data.get("toolchain") if isinstance(data.get("toolchain"), str) else None,
        standing=standing,
        owner=container_repository,
        owner_source="container",
        lineage_proof={"status": "identical", "delta_paths": [], "delta_class": "EMPTY"}
        if not has_subject
        else _lineage(
            data.get("subject_compare"),
            data.get("subject_delta_paths"),
            allowlist,
            data.get("subject_delta_class") or data.get("delta_class"),
        ),
    ).sealed()


# ------------------------------------------------------------------ admission


def admit(
    binding: EvidenceBinding,
    *,
    crown_sha: str,
    root_repository: str | None,
    allowlist: dict[str, Any],
    content: bytes | None = None,
) -> ReqState | None:
    """None when the binding is admitted; else the typed REFUSED / BLOCKED state."""
    rid = binding.requirement_id
    where = f"{rid}:{binding.evidence_locator or binding.container_repository}"
    if binding.kind not in BINDING_KINDS:
        return REFUSED("EVIDENCE_NOT_DURABLE", f"{where}: unknown binding kind {binding.kind}")
    if binding.binding_digest != binding.computed_digest():
        return REFUSED("EVIDENCE_DIGEST_MISMATCH", f"{where}: binding_digest does not recompute")
    subject, container = binding.evaluated_subject_sha, binding.evidence_container_sha
    for label, value in (("evaluated_subject", subject), ("container", container)):
        if not (isinstance(value, str) and HEX40.fullmatch(value)):
            return REFUSED("EVIDENCE_SUBJECT_MUTABLE", f"{where}: {label}={value!r} is not an exact commit")
    if not is_durable(binding.evidence_locator):
        return REFUSED("EVIDENCE_NOT_DURABLE", f"{where}: locator {binding.evidence_locator!r}")
    if content is not None and binding.evidence_digest != sha256_tag(content):
        return REFUSED(
            "EVIDENCE_DIGEST_MISMATCH", f"{where}: recorded {binding.evidence_digest} != bytes {sha256_tag(content)}"
        )
    if not binding.evidence_digest:
        return REFUSED("EVIDENCE_DIGEST_MISMATCH", f"{where}: no evidence digest")
    if binding.kind == "IN_TREE_DERIVED":
        if subject != container or subject != crown_sha:
            return REFUSED("EVIDENCE_SUBJECT_SPLIT", f"{where}: in-tree evidence evaluated {subject} in {container}")
        return None
    if binding.evaluated_subject_kind == "producer_commit":
        foreign = binding.container_repository != root_repository
        if subject == container or (foreign and subject == crown_sha):
            return REFUSED(
                "EVIDENCE_CONTAINER_CLAIMS_SUBJECT",
                f"{where}: receipt names {subject} (its container {container}, crown {crown_sha}) as its subject",
            )
    proof = binding.lineage_proof
    status = proof.get("status")
    if subject == container:
        return None  # operator-local state observed at its container (no inheritance)
    if status in LINEAGE_BAD:
        return REFUSED("EVIDENCE_SUBJECT_SPLIT", f"{where}: {subject}..{container} {status}")
    if status not in LINEAGE_OK or proof.get("delta_paths") is None:
        return REFUSED(
            "EVIDENCE_LINEAGE_MISSING",
            f"{where}: {subject}..{container} status={status} delta_paths={'unobserved' if proof.get('delta_paths') is None else 'observed'}",
        )
    computed, offending = classify_delta(proof["delta_paths"], allowlist)
    if proof.get("delta_class") != computed:
        return REFUSED(
            "EVIDENCE_DELTA_MISCLAIMED", f"{where}: claimed {proof.get('delta_class')} computed {computed}"
        )
    if computed == "UNBOUNDED":
        return BLOCKED(
            "EVIDENCE_DELTA_UNBOUNDED",
            f"{where}: {subject}..{container} changes non-receipt paths {','.join(offending[:6])}",
            subject,
        )
    return None


# ------------------------------------------------------------------ observed deltas


def _delta_index(delta_doc: dict[str, Any] | None) -> dict[tuple[str, str, str], list[str]]:
    index: dict[tuple[str, str, str], list[str]] = {}
    for pair in (delta_doc or {}).get("pairs", []):
        paths = pair.get("delta_paths")
        if pair.get("status") in LINEAGE_OK and isinstance(paths, list):
            index[(str(pair.get("repository")), str(pair.get("base")), str(pair.get("head")))] = sorted(paths)
    return index


def overlay_deltas(observations: dict[str, Any], delta_doc: dict[str, Any] | None) -> dict[str, Any]:
    """A copy of ``observations`` whose receipts carry the observed ``subject_delta_paths``.

    ``delta_doc`` is ``hardening/inputs/delta-observations.json``: each pair (repository,
    producer subject, container head) observed through the compare API. A public artifact or
    an operator-local private receipt gains the paths of the pair that matches its own
    (repository, receipt subject_sha, observed head); nothing else changes, and an artifact
    with no matching pair keeps no delta (``EVIDENCE_LINEAGE_MISSING`` stays the verdict).
    """
    out = json.loads(json.dumps(observations))
    index = _delta_index(delta_doc)
    for locator, art in out.get("artifacts", {}).items():
        data = art.get("json") if isinstance(art, dict) else None
        subject = data.get("subject_sha") if isinstance(data, dict) else None
        key = (locator.partition(":")[0], str(subject), str(art.get("head_sha") if isinstance(art, dict) else None))
        if key in index and "subject_delta_paths" not in art:
            art["subject_delta_paths"] = index[key]
    private = out.get("private_repos")
    for repository, record in (private.get("repos", {}) if isinstance(private, dict) else {}).items():
        if not isinstance(record, dict):
            continue
        for receipt in record.get("receipts", []):
            try:
                subject = json.loads(receipt.get("content", "")).get("subject_sha")
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
            key = (repository, str(subject), str(record.get("head_sha")))
            if key in index and "subject_delta_paths" not in receipt:
                receipt["subject_delta_paths"] = index[key]
    return out
