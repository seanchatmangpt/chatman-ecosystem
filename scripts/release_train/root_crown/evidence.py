"""Evidence evaluators: one per ``evidence_kind`` in requirements.json.

Each evaluator is a pure function of (requirement, context) -> ReqState. Remote
evidence is read only from ``context.observations`` (produced outside the court by
``scripts/observe_release_heads.py``); local evidence is read from the crown subject's
own tree (``context.root``). No evaluator touches the network or spawns a process.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from scripts import verify_release  # type: ignore[attr-defined]
from scripts.release_train.cross_product_court.io import load_case, receipt_dict
from scripts.release_train.release_closure_court.court import evaluate as closure_evaluate

from . import berthier, projector
from . import policy as terminality
from .model import BLOCKED, BROKEN_TERMS, FAILURE_CLASSES, PASS, REFUSED, ReqState, Requirement, sha256_bytes
from .requirements import premise_sections

LINEAGE_OK = {"identical", "ahead"}
LINEAGE_BAD = {"behind", "diverged"}
# RFC-0004 §38: FINAL | SUPERSEDED(successor) | BLOCKED(reason) | UNSUPPORTED(capability_gap) | REFUSED(type).
# The non-success members are terminal only when typed: a type, a Chatman broken_term, an
# RFC §39 failure class and an owner (and a successor for SUPERSEDED).
TYPED_TERMINAL = {"SUPERSEDED", "BLOCKED", "UNSUPPORTED", "REFUSED"}
SUCCESS_TERMINAL = {"ALIVE", "FINAL"}
# Standings the release closure court tolerates that RFC §38 does not list as terminal.
NON_TERMINAL_IMPL = {"PARTIAL_ALIVE", "PLANNED", "NOT_CLAIMED"}
_TOKEN_SPLIT = str.maketrans({c: " " for c in ";:,()[]{}|/@= \t\n"})
WORKTREE_FRESHNESS = timedelta(hours=12)
# Operator-local observations (AC-09 worktrees, private repos) share one freshness bound.
OPERATOR_LOCAL_FRESHNESS = WORKTREE_FRESHNESS


def _parse_time(value: Any) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def admit_private(observations: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, ReqState]]:
    """Admit operator-local private-repo observations (``observations/private-repos.json``).

    Returns (repo overlays, artifact overlays, typed failures per repository). A record is
    admitted only when the publicly scoped observation of its repository failed, it is no
    older than OPERATOR_LOCAL_FRESHNESS (else BLOCKED OBSERVATION_STALE), every recorded
    receipt's bytes recompute to its sha256 and git blob sha (else REFUSED
    PRIVATE_OBSERVATION_DIGEST_MISMATCH), and the recorded head is identical-to or an
    ancestor-of any publicly observed head (else REFUSED PRIVATE_HEAD_SPLIT).
    """
    private = observations.get("private_repos")
    if not isinstance(private, dict):
        return {}, {}, {}
    public = observations.get("repos", {})
    compare = observations.get("private_public_compare", {}) or {}
    repos: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    failures: dict[str, ReqState] = {}
    for repository, record in sorted(private.get("repos", {}).items()):
        if not isinstance(record, dict):
            continue
        head = record.get("head_sha")
        status = compare.get(repository)
        if status in LINEAGE_BAD:
            failures[repository] = REFUSED(
                "PRIVATE_HEAD_SPLIT", f"{repository}: recorded head {head} is {status} of the public head", head
            )
            continue
        mismatched = []
        for receipt in record.get("receipts", []):
            if "content" not in receipt:
                continue
            raw = str(receipt["content"]).encode("utf-8")
            if hashlib.sha256(raw).hexdigest() != receipt.get("sha256") or _blob_sha(raw) != receipt.get("blob_sha"):
                mismatched.append(str(receipt.get("path")))
        if mismatched:
            failures[repository] = REFUSED(
                "PRIVATE_OBSERVATION_DIGEST_MISMATCH", f"{repository}: " + ",".join(sorted(mismatched)), head
            )
            continue
        try:
            age = _parse_time(observations.get("observed_at")) - _parse_time(
                record.get("observed_at") or private.get("observed_at")
            )
        except ValueError:
            failures[repository] = BLOCKED("OBSERVATION_STALE", f"{repository}: unparseable observed_at")
            continue
        if age > OPERATOR_LOCAL_FRESHNESS:
            failures[repository] = BLOCKED(
                "OBSERVATION_STALE",
                f"{repository}: operator-local observation {record.get('observed_at')} older than {OPERATOR_LOCAL_FRESHNESS}",
            )
            continue
        if (
            record.get("observer") != "operator-local"
            or record.get("error")
            or not (isinstance(head, str) and len(head) == 40)
        ):
            failures[repository] = BLOCKED(
                "OBSERVATION_MISSING", f"{repository}: operator-local record unusable ({record.get('error')})"
            )
            continue
        if not public.get(repository, {}).get("error") and public.get(repository, {}).get("head_sha"):
            continue  # publicly observable: the public observation stays primary
        repos[repository] = {
            key: record.get(key) for key in ("pin_sha", "default_branch", "head_sha", "compare_status", "visibility")
        } | {"source": "operator-local"}
        for receipt in record.get("receipts", []):
            locator = f"{repository}:{receipt.get('path')}"
            if receipt.get("error"):
                artifacts[locator] = {"error": receipt["error"], "head_sha": head}
                continue
            entry: dict[str, Any] = {
                "sha256": receipt.get("sha256"),
                "blob_sha": receipt.get("blob_sha"),
                "head_sha": head,
                "source": "operator-local",
            }
            try:
                entry["json"] = json.loads(receipt["content"])
            except (KeyError, json.JSONDecodeError):
                pass
            if receipt.get("subject_compare"):
                entry["subject_compare"] = receipt["subject_compare"]
            artifacts[locator] = entry
    return repos, artifacts, failures


def standing_of(data: dict[str, Any]) -> tuple[str | None, str, str | None]:
    """(state, inline type, inline broken_term) of a receipt's ``standing``.

    Accepts the flat form (``"standing": "BLOCKED"``) and the Chatman receipt form
    (``~/.claude/dfcm/receipt.schema.json``: ``{"value": "BLOCKED:<reason>" | "REFUSED(<type>)"
    | "UNSUPPORTED(<gap>)" | ..., "derived_from": ..., "broken_term": ...}``).
    """
    raw = data.get("standing")
    broken = None
    if isinstance(raw, dict):
        broken = raw.get("broken_term")
        raw = raw.get("value")
    if not isinstance(raw, str) or not raw.strip():
        return None, "", broken
    value = raw.strip()
    for sep in ("(", ":"):
        head, found, rest = value.partition(sep)
        if found and head.isupper():
            return head, rest.rstrip(")").strip(), broken
    return value, "", broken


def _tokens(*texts: Any) -> set[str]:
    return {t for text in texts if isinstance(text, str) for t in text.translate(_TOKEN_SPLIT).split()}


def typing_gaps(
    record: dict[str, Any],
    state: str,
    *,
    type_text: str = "",
    broken_term: Any = None,
    owner: Any = None,
) -> list[str]:
    """What a non-success terminal disposition lacks to be typed (RFC §38 + §39 + §36 owner).

    Returns [] when typed. ``type_text`` is the disposition's reason/type; broken_term and the
    §39 class are read from explicit fields first, then from tokens of the type text.
    """
    gaps: list[str] = []
    if not str(type_text).strip():
        gaps.append("type")
    tokens = _tokens(type_text)
    terms = {record.get("broken_term"), broken_term} | tokens
    if not terms & set(BROKEN_TERMS):
        gaps.append("broken_term")
    classes = {record.get("failure_class"), record.get("class")} | tokens
    if not classes & set(FAILURE_CLASSES):
        gaps.append("failure_class")
    if not (isinstance(owner, str) and owner.strip()):
        gaps.append("owner")
    if state == "SUPERSEDED":
        successor = record.get("successor")
        if not (isinstance(successor, dict) and successor.get("sha")) and not (
            isinstance(successor, str) and successor.strip()
        ):
            gaps.append("successor")
    return gaps


# Receipt fields that may name an owner explicitly (RFC §36). The owner of a receipt is the
# repository that contains it (the container); an explicit owner must equal the container.
OWNER_KEYS = ("owner", "owner_repo", "repo", "repository")


def resolve_owner(
    data: dict[str, Any], container: str | None, keys: tuple[str, ...] = OWNER_KEYS
) -> tuple[str | None, str, ReqState | None]:
    """(owner, owner_source, OWNER_SPLIT refusal | None).

    An explicit owner field must equal the container repository, else REFUSED OWNER_SPLIT
    (a receipt cannot speak for a repository it does not live in). Without an explicit
    owner the container repository is the owner (``owner_source=container``); with no
    container either, the owner is absent and ``typing_gaps`` names it.
    """
    explicit = sorted({str(data[k]).strip() for k in keys if isinstance(data.get(k), str) and str(data[k]).strip()})
    if explicit:
        wrong = [e for e in explicit if e != container]
        if wrong:
            return None, "explicit", REFUSED("OWNER_SPLIT", f"owner={','.join(wrong)} container={container}")
        return container, "explicit", None
    if isinstance(container, str) and container.strip():
        return container, "container", None
    return None, "absent", None


@dataclass
class Context:
    root: Path
    release_dir: Path
    observations: dict[str, Any]
    crown_sha: str
    inputs: projector.Inputs
    premise_text: str | None = None  # in-memory override (crown test)
    extra: dict[str, Any] = field(default_factory=dict)
    policy_root: Path = terminality.POLICY_ROOT
    private_failures: dict[str, ReqState] = field(init=False)
    policy: terminality.Policy | None = field(init=False, default=None)
    policy_missing: str | None = field(init=False, default=None)
    _repos: dict[str, Any] = field(init=False, repr=False)
    _artifacts: dict[str, Any] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        repos, artifacts, self.private_failures = admit_private(self.observations)
        self._repos = dict(self.observations.get("repos", {})) | repos
        self._artifacts = dict(self.observations.get("artifacts", {})) | artifacts
        try:
            self.policy = terminality.load_policy(self.release_dir.name, self.policy_root)
        except terminality.PolicyMissing as exc:
            self.policy, self.policy_missing = None, str(exc)

    @property
    def import_sha256(self) -> str | None:
        """sha256 IMPORTS.json records for the pinned RFC-0004 import (None when not exactly one)."""
        rfc = [i for i in self.inputs.imports.get("imports", []) if i.get("path") == "imports/RFC-0004.md"]
        return str(rfc[0].get("sha256")) if len(rfc) == 1 else None

    @property
    def container_repo(self) -> str | None:
        """The repository that contains local (``local:``) evidence: the crown's root repository."""
        return self.inputs.pins.get("root_repository")

    def policy_row(self, req: Requirement) -> tuple[terminality.Row | None, ReqState | None]:
        return terminality.admit(
            self.policy, self.policy_missing, req.id, req.acceptance, self.inputs.rfc_text, self.import_sha256
        )

    def policy_refusals(self) -> list[str]:
        return terminality.validate(
            self.policy,
            self.policy_missing,
            self.inputs.requirements_doc.get("requirements", []),
            self.inputs.rfc_text,
            self.import_sha256,
        )

    @property
    def repos(self) -> dict[str, Any]:
        return self._repos

    @property
    def artifacts(self) -> dict[str, Any]:
        return self._artifacts

    def private_failure(self, repositories: Any) -> ReqState | None:
        """First typed private-observation failure among ``repositories`` (refusals first)."""
        hits = [self.private_failures[r] for r in sorted(set(repositories)) if r in self.private_failures]
        return next((h for h in hits if h.state == "REFUSED"), hits[0] if hits else None)


def _local_path(ctx: Context, req: Requirement) -> Path:
    return ctx.root / req.evidence_locator[len("local:") :]


def manifest_valid(req: Requirement, ctx: Context) -> ReqState:
    path = ctx.release_dir / "manifest.toml"
    if not path.is_file():
        return REFUSED("MANIFEST_INVALID", f"absent:{path.as_posix()}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return REFUSED("MANIFEST_INVALID", f"toml:{exc}")
    findings = verify_release.validate_manifest(data, Path("release") / ctx.release_dir.name / "manifest.toml")
    if findings:
        return REFUSED("MANIFEST_INVALID", ";".join(f"{f.code}:{f.subject}" for f in findings))
    return PASS(f"manifest sha256={sha256_bytes(path.read_bytes())}", ctx.crown_sha)


def closure_terminal(req: Requirement, ctx: Context) -> ReqState:
    """AC-02 / F-03: every required subject has a terminal disposition (RFC §5, §37, §38, §47.3).

    The admitted terminal states come from the terminality policy row of ``req`` (AC-02 and
    F-03 admit ALIVE/FINAL and typed SUPERSEDED/BLOCKED/UNSUPPORTED/REFUSED, grounded by RFC
    §48 "all required subjects terminal" and §47 "A required subject remains UNKNOWN"). A
    typed row carries type + broken_term + §39 class + owner, and its owner is its
    ``repository`` (an explicit ``owner`` naming another repository is OWNER_SPLIT). UNKNOWN
    or an untyped row is REFUSED; a lawful-but-non-terminal row (PARTIAL_ALIVE, PLANNED,
    NOT_CLAIMED) or a typed state the policy does not admit keeps the closure BLOCKED.
    """
    policy_row, refusal = ctx.policy_row(req)
    if refusal is not None:
        return refusal
    assert policy_row is not None
    verdict = closure_evaluate(ctx.inputs.closure)
    receipt = verdict.receipt["receipt_digest"]
    if verdict.standing == "REFUSED":
        return REFUSED("SUBJECT_NOT_TERMINAL", ";".join(verdict.refusals))
    untyped: list[str] = []
    splits: list[str] = []
    open_rows: list[str] = []
    typed = 0
    required = [r for r in ctx.inputs.closure.get("subjects", []) if r.get("required", True)]
    for row in required:
        sid = row.get("subject_id")
        for label in ("spec", "impl"):
            state = row.get(f"{label}_standing")
            if label == "impl" and state in NON_TERMINAL_IMPL:
                open_rows.append(f"{sid}:{label}={state}")
            elif state in TYPED_TERMINAL:
                if not policy_row.admits(state):
                    open_rows.append(f"{sid}:{label}={state}:not-admitted-by-policy({req.id})")
                    continue
                owner, _, split = resolve_owner(row, row.get("repository"), ("owner",))
                if split is not None:
                    splits.append(f"{sid}:{split.detail}")
                    continue
                gaps = typing_gaps(
                    row,
                    state,
                    type_text=str(row.get(f"{label}_type", "")),
                    broken_term=row.get(f"{label}_broken_term"),
                    owner=owner,
                )
                if gaps:
                    untyped.append(f"{sid}:{label}={state}:missing={'+'.join(gaps)}")
                else:
                    typed += 1
    if untyped:
        return REFUSED("SUBJECT_NOT_TERMINAL", "untyped terminal disposition: " + ",".join(sorted(untyped)))
    if splits:
        return REFUSED("OWNER_SPLIT", ",".join(sorted(splits)))
    if open_rows:
        return BLOCKED(
            "CLOSURE_PARTIAL",
            f"closure {verdict.standing}; non-terminal={','.join(sorted(open_rows))}; receipt={receipt}",
        )
    return PASS(
        f"{len(required)} required subjects terminal ({typed} typed non-ALIVE dispositions); "
        f"closure court {verdict.standing}; receipt={receipt}; policy {req.id} ceiling={policy_row.standing_ceiling}",
        ctx.crown_sha,
    )


def _premise_origin(ctx: Context) -> str | None:
    """None when the imported premise has one FINAL_SPEC owner and a byte-identical import."""
    imports = ctx.inputs.imports.get("imports", [])
    rfc = [i for i in imports if i.get("path") == "imports/RFC-0004.md"]
    if len(rfc) != 1:
        return f"imports:{len(rfc)}-RFC-0004-entries"
    entry = rfc[0]
    text = ctx.premise_text if ctx.premise_text is not None else ctx.inputs.rfc_text
    if sha256_bytes(text.encode("utf-8")) != entry.get("sha256"):
        return "import-sha256-mismatch"
    owners = {
        (r.get("repository"), r.get("artifact"))
        for r in ctx.inputs.closure.get("subjects", [])
        if r.get("rfc_id") == "RFC-0004" and r.get("spec_standing") == "FINAL_SPEC"
    }
    if owners != {(entry.get("source_repo"), entry.get("source_path"))}:
        return f"final-spec-owners={sorted(map(str, owners))}"
    observed = ctx.artifacts.get(f"{entry['source_repo']}:{entry['source_path']}@{entry['source_sha']}")
    if observed is not None and observed.get("sha256") not in (None, entry.get("sha256")):
        return "source-blob-sha256-mismatch"
    return None


def origin_authority(req: Requirement, ctx: Context) -> ReqState:
    problem = _premise_origin(ctx)
    if problem is not None:
        return REFUSED("ORIGIN_AUTHORITY_NOT_UNIQUE", problem)
    return receipt_artifact(req, ctx)


def _artifact(req: Requirement, ctx: Context) -> tuple[dict[str, Any] | None, ReqState | None, bool]:
    """(json, blocker, is_local)."""
    if req.evidence_locator.startswith("local:"):
        path = _local_path(ctx, req)
        if not path.is_file():
            return None, BLOCKED("EVIDENCE_ABSENT", f"absent:{req.evidence_locator}"), True
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None, BLOCKED("ARTIFACT_NOT_JSON", req.evidence_locator), True
        return data, None, True
    repo = req.locator_repo
    failure = ctx.private_failure([repo])
    if failure is not None:
        return None, failure, False
    observed = ctx.artifacts.get(req.evidence_locator)
    if observed is None:
        repo_obs = ctx.repos.get(repo or "", {})
        if repo_obs.get("error") or not repo_obs:
            return None, BLOCKED("OBSERVATION_MISSING", f"{repo}:{repo_obs.get('error', 'not-observed')}"), False
        return None, BLOCKED("EVIDENCE_ABSENT", f"not-observed:{req.evidence_locator}"), False
    if observed.get("error"):
        code = "EVIDENCE_ABSENT" if "404" in str(observed["error"]) else "OBSERVATION_MISSING"
        return None, BLOCKED(code, f"{req.evidence_locator}:{observed['error']}"), False
    data = observed.get("json")
    if not isinstance(data, dict):
        return None, BLOCKED("ARTIFACT_NOT_JSON", req.evidence_locator), False
    return data, None, False


def _bound(req: Requirement, ctx: Context, data: dict[str, Any], is_local: bool, standing: str | None) -> ReqState:
    """PASS only when the artifact names its subject and that subject is on the owner's lineage.

    The detail names the receipt's own standing (a typed BLOCKED receipt is "BLOCKED at
    <subject>", never "ALIVE at").
    """
    if is_local:
        return PASS(f"local artifact {req.evidence_locator} ({standing})", ctx.crown_sha)
    subject = data.get("subject_sha")
    if not subject and isinstance(data.get("subject"), dict):
        subject = data["subject"].get("sha")
    if not isinstance(subject, str) or len(subject) != 40:
        return BLOCKED("ARTIFACT_UNBOUND", f"{req.evidence_locator}: no subject_sha")
    status = ctx.artifacts.get(req.evidence_locator, {}).get("subject_compare")
    if status in LINEAGE_BAD:
        return REFUSED("ARTIFACT_SUBJECT_SPLIT", f"{req.evidence_locator}:{subject}:{status}", subject)
    if status not in LINEAGE_OK:
        return BLOCKED("OBSERVATION_MISSING", f"{req.evidence_locator}: subject lineage unobserved", subject)
    return PASS(f"{req.evidence_locator} {standing} at {subject} ({status})", subject)


def _typed_terminal(
    req: Requirement,
    ctx: Context,
    data: dict[str, Any],
    is_local: bool,
    standing: str,
    inline: tuple[str, Any],
    row: terminality.Row,
    anchor: str,
) -> ReqState:
    """A typed RFC §38 disposition admitted by the policy row: typed, owned by its container, bound."""
    container = ctx.container_repo if is_local else req.locator_repo
    owner, source, split = resolve_owner(data, container)
    if split is not None:
        return REFUSED("OWNER_SPLIT", f"{req.evidence_locator}:{split.detail}")
    inline_type, inline_term = inline
    type_text = " ".join(str(x) for x in (data.get("type") or data.get("blocked_type"), inline_type) if x)
    gaps = typing_gaps(data, standing, type_text=type_text, broken_term=inline_term, owner=owner)
    if gaps:
        return REFUSED("BLOCKED_WITHOUT_TYPE", f"{req.evidence_locator}:{standing}:missing={'+'.join(gaps)}")
    bound = _bound(req, ctx, data, is_local, standing)
    if bound.state != "PASS":
        return bound
    kind = data.get("type") or data.get("blocked_type") or inline_type
    return PASS(
        f"terminal {standing}({kind}) ({anchor}; policy {req.id} ceiling={row.standing_ceiling}); "
        f"owner={owner} owner_source={source}; {bound.detail}",
        bound.subject_sha,
    )


def receipt_artifact(req: Requirement, ctx: Context) -> ReqState:
    """The requirement's terminality policy row decides which receipt standings are terminal.

    Capability rows admit ALIVE only: the receipt must be ALIVE and bound to a merged SHA.
    Relaxed rows (AC-15) also admit a typed SUPERSEDED/BLOCKED/UNSUPPORTED/REFUSED
    disposition bound the same way. A required receipt that is UNKNOWN is REFUSED (RFC §5:
    a required release subject MUST NOT remain UNKNOWN; §47 falsifier 3).
    """
    policy_row, refusal = ctx.policy_row(req)
    if refusal is not None:
        return refusal
    assert policy_row is not None
    data, blocker, is_local = _artifact(req, ctx)
    if blocker is not None:
        return blocker
    assert data is not None
    standing, inline_type, inline_term = standing_of(data)
    if standing == "UNKNOWN" and req.required:
        return REFUSED("REQUIRED_UNKNOWN", f"{req.evidence_locator}: standing UNKNOWN")
    kind = data.get("type") or data.get("blocked_type") or inline_type or "untyped"
    if standing in SUCCESS_TERMINAL and policy_row.admits(standing):
        return _bound(req, ctx, data, is_local, standing)
    if standing in TYPED_TERMINAL and policy_row.admits(standing):
        return _typed_terminal(req, ctx, data, is_local, standing, (inline_type, inline_term), policy_row, "RFC §38")
    if standing == "REFUSED":
        return REFUSED("ARTIFACT_REFUSED", f"{req.evidence_locator}:{data.get('refusals') or kind}")
    return BLOCKED(
        "ARTIFACT_BLOCKED",
        f"{req.evidence_locator}:{standing}({kind}) not terminal for {req.id} "
        f"(policy admits {'|'.join(policy_row.allowed_terminal_states)})",
    )


def typed_blocker_allowed(req: Requirement, ctx: Context) -> ReqState:
    """RFC §55 cloud_runtime_alive_or_typed_blocker (F-09).

    An ALIVE claim needs a transport and an execution receipt and a merged subject. A
    non-success standing is lawful only when the policy row admits it (F-09: BLOCKED,
    UNSUPPORTED) and it is typed (type + broken_term + §39 class + owner = container repo)
    and bound to a merged subject; anything else is REFUSED or stays BLOCKED.
    """
    f09_row, refusal = ctx.policy_row(req)
    if refusal is not None:
        return refusal
    assert f09_row is not None
    data, blocker, is_local = _artifact(req, ctx)
    if blocker is not None:
        return blocker
    assert data is not None
    standing, inline_type, inline_term = standing_of(data)
    if req.required and standing == "UNKNOWN":
        return REFUSED("REQUIRED_UNKNOWN", f"{req.evidence_locator}: standing UNKNOWN")
    if standing == "ALIVE" and f09_row.admits(standing):
        if not data.get("transport_receipt") or not data.get("execution_receipt"):
            return REFUSED(
                "CLAIM_WITHOUT_RECEIPT", f"{req.evidence_locator}: ALIVE without transport+execution receipt"
            )
        return _bound(req, ctx, data, is_local, standing)
    if standing in TYPED_TERMINAL and f09_row.admits(standing):
        return _typed_terminal(req, ctx, data, is_local, standing, (inline_type, inline_term), f09_row, "RFC §55")
    if standing == "REFUSED":
        return REFUSED("ARTIFACT_REFUSED", f"{req.evidence_locator}")
    return BLOCKED(
        "ARTIFACT_BLOCKED",
        f"{req.evidence_locator}:{standing} not admitted for {req.id} "
        f"(policy admits {'|'.join(f09_row.allowed_terminal_states)})",
    )


def berthier_court(req: Requirement, ctx: Context) -> ReqState:
    verdict = judge_committed(ctx)
    if verdict.refusals:
        return REFUSED("BERTHIER_COURT_FAILED", ";".join(verdict.refusals[:8]))
    ok, detail = crown_test(ctx.inputs)
    if not ok:
        return REFUSED("BERTHIER_COURT_FAILED", f"RFC §9 crown test: {detail}")
    return PASS(f"berthier ALIVE; RFC §9 crown test: {detail}", ctx.crown_sha)


def judge_committed(ctx: Context, rfc_text: str | None = None) -> berthier.BerthierVerdict:
    inputs = ctx.inputs
    graph = inputs.prior_berthier or {"edges": [], "baseline": {}}
    edges = berthier.edges_from_json(graph["edges"])
    text = rfc_text if rfc_text is not None else (ctx.premise_text if ctx.premise_text is not None else inputs.rfc_text)
    current = berthier.source_digests(text, inputs.requirements)
    for name in berthier.PROJECTED_OUTPUTS:
        path = ctx.release_dir / name
        if path.is_file():
            current[f"proj:{name}"] = sha256_bytes(path.read_bytes())
    packets_path = ctx.release_dir / "out/packets.json"
    declared = json.loads(packets_path.read_text(encoding="utf-8"))["packets"] if packets_path.is_file() else []
    observed = {
        berthier.artifact_key(k): v.get("sha256")
        for k, v in ctx.artifacts.items()
        if isinstance(v, dict) and v.get("sha256")
    }
    return berthier.judge(
        edges,
        current,
        declared,
        graph.get("baseline", {}),
        observed,
        ctx.observations.get("live_runtime_failures", []),
    )


def crown_test(inputs: projector.Inputs, section: str | None = None) -> tuple[bool, str]:
    """RFC-0004 §9, in memory: mutate one premise section once, re-run analysis, regenerate.

    Returns (ok, detail). ok requires: the committed graph refuses STALE_PROJECTION for
    exactly the independently computed dependents of the mutated section; re-projection
    from the mutated premise alone is ALIVE; its packets cover exactly the owners of the
    affected requirements; and no other input changed (ManualRestatementCount = 0).
    """
    sections = premise_sections(inputs.rfc_text)
    referenced = sorted({ref for r in inputs.requirements for ref in r.premise_refs})
    owners_by_section = {
        ref: len({r.owner_repo for r in inputs.requirements if ref in r.premise_refs}) for ref in referenced
    }
    # Default: the referenced section whose change fans out to the most owner repositories.
    target = section or (max(referenced, key=lambda ref: (owners_by_section[ref], ref)) if referenced else None)
    if target is None or target not in sections:
        return False, "no referenced premise section"
    original = sections[target]
    mutated_section = original + "\n(mutated once: strategic objective changed)"
    mutated_text = inputs.rfc_text.replace(original, mutated_section, 1)
    affected = sorted(r.id for r in inputs.requirements if target in r.premise_refs)
    expected = set()
    for rid in affected:
        req = next(r for r in inputs.requirements if r.id == rid)
        expected |= {
            berthier.req_key(rid),
            berthier.packet_key(req.owner_repo),
            berthier.artifact_key(req.evidence_locator),
        }
        expected |= {f"proj:{o}" for o in berthier.PROJECTED_OUTPUTS}
    graph = inputs.prior_berthier
    if graph is None:
        return False, "no committed berthier.json"
    edges = berthier.edges_from_json(graph["edges"])
    current = berthier.source_digests(mutated_text, inputs.requirements)
    stale_verdict = berthier.judge(edges, current, [], {}, None)
    if set(stale_verdict.stale) != expected:
        return False, f"stale={sorted(stale_verdict.stale)} expected={sorted(expected)}"
    rows_before = berthier.digest(inputs.requirements_doc)
    pins_before = berthier.digest(inputs.pins)
    regenerated = projector.compile_graph(inputs, rfc_text=mutated_text)
    new_graph = json.loads(regenerated["berthier.json"])
    new_packets = json.loads(regenerated["out/packets.json"])["packets"]
    new_current = berthier.source_digests(mutated_text, inputs.requirements)
    new_current["proj:out/packets.json"] = sha256_bytes(regenerated["out/packets.json"])
    new_current["proj:out/requirements.ttl"] = sha256_bytes(regenerated["out/requirements.ttl"])
    after = berthier.judge(
        berthier.edges_from_json(new_graph["edges"]), new_current, new_packets, new_graph["baseline"], None
    )
    owners = sorted({next(r for r in inputs.requirements if r.id == rid).owner_repo for rid in affected})
    # Restatement = any hand-written input other than the premise having to change.
    manual_restatements = int(berthier.digest(inputs.requirements_doc) != rows_before) + int(
        berthier.digest(inputs.pins) != pins_before
    )
    if manual_restatements:
        return False, f"ManualRestatementCount={manual_restatements}"
    if after.refusals:
        return False, f"recompile refused {after.refusals[:4]}"
    if list(after.required_owners) != owners:
        return False, f"packets owners={list(after.required_owners)} expected={owners}"
    return True, (
        f"section={target} dependents={len(expected)} affected={affected} owners={owners} "
        f"ManualRestatementCount={manual_restatements}"
    )


def xprod_case(req: Requirement, ctx: Context) -> ReqState:
    path = _local_path(ctx, req)
    if not path.is_file():
        return BLOCKED("EVIDENCE_ABSENT", f"absent:{req.evidence_locator}")
    try:
        receipt = receipt_dict(load_case(path))
    except (KeyError, ValueError, TypeError) as exc:
        return REFUSED("XPROD_REFUSED", f"inadmissible case: {exc}")
    standing = receipt["standing"]
    if standing == "REFUSED":
        return REFUSED("XPROD_REFUSED", ";".join(receipt.get("refusals", [])[:6]))
    if standing != "ALIVE":
        return BLOCKED("XPROD_BLOCKED", f"{standing}:{';'.join(receipt.get('refusals', [])[:6])}")
    # Producer binding: every case subject must be a merged SHA (on its default-branch lineage).
    lineage = ctx.observations.get("subjects", {})
    split, unobserved = [], []
    for identity in receipt.get("subject_bindings", []):
        status = lineage.get(identity)
        if status in LINEAGE_BAD:
            split.append(f"{identity}:{status}")
        elif status not in LINEAGE_OK:
            unobserved.append(identity)
    if split:
        return REFUSED("XPROD_REFUSED", "producer subject not merged: " + ",".join(split))
    if unobserved:
        return BLOCKED("OBSERVATION_MISSING", "producer subject lineage unobserved: " + ",".join(unobserved))
    return PASS(f"XPROD ALIVE receipt={receipt.get('receipt_digest')}", ctx.crown_sha)


def _transient_shas(ctx: Context) -> set[str]:
    shas = {t.get("sha") for t in ctx.inputs.closure.get("transient_heads", [])}
    for line in ctx.root.glob("release/*/closure.json"):
        try:
            data = json.loads(line.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        shas |= {t.get("sha") for t in data.get("transient_heads", [])}
    return {s for s in shas if s}


def durable_pins(req: Requirement, ctx: Context) -> ReqState:
    failure = ctx.private_failure(p["repository"] for p in ctx.inputs.pins["repos"].values())
    if failure is not None:
        return failure
    transient = _transient_shas(ctx)
    hits = sorted(f"{p['repository']}@{p['sha']}" for p in ctx.inputs.pins["repos"].values() if p["sha"] in transient)
    if hits:
        return REFUSED("TRANSIENT_DEPENDENCY", ",".join(hits))
    unobserved = sorted(
        p["repository"]
        for p in ctx.inputs.pins["repos"].values()
        if not p.get("root")
        and (ctx.repos.get(p["repository"], {}).get("compare_status") not in LINEAGE_OK | LINEAGE_BAD)
    )
    if unobserved:
        return BLOCKED("OBSERVATION_MISSING", "pins unobserved: " + ",".join(unobserved))
    return PASS(f"{len(ctx.inputs.pins['repos'])} pins durable", ctx.crown_sha)


def merged_sha(req: Requirement, ctx: Context) -> ReqState:
    failure = ctx.private_failure(p["repository"] for p in ctx.inputs.pins["repos"].values())
    if failure is not None:
        return failure
    bad, missing = [], []
    for pin in ctx.inputs.pins["repos"].values():
        if pin.get("root"):
            continue
        obs = ctx.repos.get(pin["repository"], {})
        status = obs.get("compare_status")
        if obs.get("pin_sha") not in (None, pin["sha"]):
            bad.append(f"{pin['repository']}:observed-pin={obs.get('pin_sha')}")
        elif status in LINEAGE_BAD:
            bad.append(f"{pin['repository']}@{pin['sha']}:{status}")
        elif status not in LINEAGE_OK:
            missing.append(f"{pin['repository']}:{obs.get('error', 'unobserved')}")
    if bad:
        return REFUSED("SHA_NOT_MERGED", ",".join(sorted(bad)))
    if missing:
        return BLOCKED("OBSERVATION_MISSING", ",".join(sorted(missing)))
    return PASS("every pin identical-to or ancestor-of its default-branch head", ctx.crown_sha)


def cold_reconstruction(req: Requirement, ctx: Context) -> ReqState:
    drift = projector.check(ctx.release_dir)
    if drift:
        return REFUSED("COLD_RECONSTRUCTION_DIVERGED", ",".join(drift))
    env = ctx.observations.get("environment", {})
    if not env.get("cold"):
        return BLOCKED("NOT_COLD", "projection current but evaluation environment not declared cold (clean runner)")
    return PASS(f"cold projector --check current (run {env.get('run_id')})", ctx.crown_sha)


def worktree_observation(req: Requirement, ctx: Context) -> ReqState:
    local = ctx.observations.get("local_worktrees")
    if not isinstance(local, dict):
        return BLOCKED("EVIDENCE_ABSENT", "no operator-local worktree observation")
    worktrees = local.get("worktrees")
    if not isinstance(worktrees, list):
        return BLOCKED("EVIDENCE_ABSENT", f"local observation lacks a worktree list ({local.get('source')})")
    try:
        seen = _parse_time(local.get("observed_at"))
        now = _parse_time(ctx.observations.get("observed_at"))
    except ValueError:
        return BLOCKED("OBSERVATION_STALE", "unparseable observed_at")
    if now - seen > WORKTREE_FRESHNESS:
        return BLOCKED(
            "OBSERVATION_STALE", f"local observation {local.get('observed_at')} older than {WORKTREE_FRESHNESS}"
        )
    allow = ctx.inputs.allow.get("allow", {})
    unauthorized = sorted(
        f"{w.get('repo')}:{w.get('path')}" for w in worktrees if w.get("path") not in allow.get(w.get("repo"), [])
    )
    if unauthorized:
        return REFUSED("UNAUTHORIZED_WORKTREE", f"{len(unauthorized)}: " + ",".join(unauthorized[:10]))
    return PASS(f"0 unauthorized worktrees ({local.get('source')})", ctx.crown_sha)


def tag_binding(req: Requirement, ctx: Context) -> ReqState:
    tag = ctx.observations.get("tag")
    if not isinstance(tag, dict) or "sha" not in tag:
        return BLOCKED("OBSERVATION_MISSING", "tag not observed")
    if tag["sha"] is None:
        return PASS(f"{tag.get('name')} absent; tag job binds it to crown_sha only after ALIVE", ctx.crown_sha)
    if tag["sha"] != ctx.crown_sha:
        return REFUSED("TAG_SHA_SPLIT", f"{tag.get('name')}={tag['sha']} crown={ctx.crown_sha}")
    return PASS(f"{tag.get('name')}={tag['sha']} == crown_sha", ctx.crown_sha)


def crown_self(req: Requirement, ctx: Context) -> ReqState:
    # Evaluated by crown.py after every other requirement (needs their states).
    states: dict[str, ReqState] = ctx.extra.get("states", {})
    open_ids = sorted(k for k, v in states.items() if k != req.id and v.state != "PASS")
    if open_ids:
        return BLOCKED("CROWN_DEPENDENCIES_OPEN", ",".join(open_ids))
    return PASS("every other requirement PASS", ctx.crown_sha)


Evaluator = Callable[[Requirement, Context], ReqState]

EVALUATORS: dict[str, Evaluator] = {
    "manifest_valid": manifest_valid,
    "closure_terminal": closure_terminal,
    "origin_authority": origin_authority,
    "receipt_artifact": receipt_artifact,
    "typed_blocker_allowed": typed_blocker_allowed,
    "berthier_court": berthier_court,
    "xprod_case": xprod_case,
    "durable_pins": durable_pins,
    "merged_sha": merged_sha,
    "cold_reconstruction": cold_reconstruction,
    "worktree_observation": worktree_observation,
    "tag_binding": tag_binding,
    "crown_self": crown_self,
}
DEFERRED = {"crown_self"}
