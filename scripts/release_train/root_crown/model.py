"""Root crown data model: requirements, requirement states, rule table.

RFC-0004 (engineering-standards@7e8d4c5c) §3: RELEASE = C ∧ A ∧ R ∧ X ∧ F ∧ M; RFC-0005
(engineering-standards@71a6f607) adds ∧ U from the next calver. The evaluated term set is
the one the release premise declares (``release_terms``), never a hard-coded tuple.
Every refusal/blocker code the root crown can emit is listed in ``FAILURE_CLASS``
with its RFC §39 class and its Chatman-equation ``broken_term``; a test asserts
the table is total over every emitted code.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from scripts.release_train.cross_product_court.model import canonical_digest

SCHEMA_RECEIPT = "https://chatman.dev/root-crown/receipt/v1"
# v2 (post-tag hardening): mode, subject{tag,tag_object_sha,commit_sha,tree_sha},
# attestation_head_sha, historical, current. verify_receipt accepts v1 and v2.
SCHEMA_RECEIPT_V2 = "https://chatman.dev/root-crown/receipt/v2"
SCHEMA_RECEIPTS = (SCHEMA_RECEIPT, SCHEMA_RECEIPT_V2)
MODES = ("PRE_TAG", "POST_TAG")
SCHEMA_OBSERVATIONS = "https://chatman.dev/root-crown/observations/v1"

# RFC-0004 §3 base theorem. A release premise may declare more terms (requirements.json
# ``terms``); ``release_terms`` computes the evaluated set and the crown never iterates a
# fixed tuple. A premise without a ``terms`` table evaluates exactly these six.
TERMS = ("C", "A", "R", "X", "F", "M")
# Every term symbol the crown can evaluate, in theorem order.
TERM_REGISTRY = TERMS + ("U",)
TERM_NAMES = {
    "C": "closure",
    "A": "authority integrity",
    "R": "receipts and replay",
    "X": "semantic cross-product verification",
    "F": "formalized recurring reasoning",
    "M": "migration and repository integrity",
    "U": "autonomic closure",
}
# Terms bound by a premise other than RFC-0004 (RFC-0005 §10 premise set): their rows cite
# ``<RFC>§n`` references and are admitted against that premise, not RFC-0004 coverage.
TERM_PREMISE = {"U": "RFC-0005"}
# RFC-0005 §2.2-§2.3: U SHALL NOT be evaluated for v26.9.25 and binds from the next calver
# onward: a premise that declares U earlier is refused, and a premise for a release on or
# after the first calver that omits U is refused while U is still evaluated (no silent drop).
TERM_FROM_RELEASE = {"U": (26, 9, 26)}
_CALVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def calver(release: Any) -> tuple[int, int, int] | None:
    """``vYY.M.D`` -> (YY, M, D); anything else -> None (no term gating)."""
    match = _CALVER.fullmatch(release) if isinstance(release, str) else None
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def release_terms(doc: dict[str, Any], release: str | None = None) -> tuple[tuple[str, ...], list[str]]:
    """(terms evaluated for this premise, typed REQ_TERM_UNBOUND / REQ_MALFORMED refusals).

    The premise's ``terms`` table declares the theorem; absent, the RFC-0004 six. A declared
    symbol outside ``TERM_REGISTRY`` is refused. ``TERM_FROM_RELEASE`` gates a term both
    ways: declared before its first calver -> refused (``premature``); omitted on or after
    it -> refused (``required-from``) and still evaluated, so its missing rows keep it open.

    Hardening (v26.9.26): the premise can only add terms, never erode the RFC-0004 base: an
    omitted base term is refused (``base-term-omitted``) and still evaluated. A ``terms``
    table that is present but not a non-empty object is refused (never silently defaulted).
    ``release`` is the release line the crown evaluates (the release directory name); a
    premise naming another line, or a line that is not a calver, is refused so the term
    gate cannot be bypassed by relabelling the premise.
    """
    refusals: list[str] = []
    table = doc.get("terms")
    if "terms" in doc and not (isinstance(table, dict) and table):
        refusals.append("REFUSED:REQ_MALFORMED:terms:not-a-non-empty-object")
    declared = list(table) if isinstance(table, dict) and table else list(TERMS)
    refusals += [f"REFUSED:REQ_TERM_UNBOUND:{t}:not-in-registry" for t in declared if t not in TERM_REGISTRY]
    evaluated = {t for t in declared if t in TERM_REGISTRY}
    for term in TERMS:
        if term not in evaluated:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{term}:base-term-omitted")
            evaluated.add(term)
    named = doc.get("release")
    line = release if release is not None else named
    if release is not None and named is not None and named != release:
        refusals.append(f"REFUSED:REQ_MALFORMED:release:premise-names-{named}-for-{release}")
    version = calver(line)
    if line is not None and version is None:
        refusals.append(f"REFUSED:REQ_MALFORMED:release:not-calver:{line}")
    for term, first in sorted(TERM_FROM_RELEASE.items()):
        since = "v{}.{}.{}".format(*first)
        if version is None:
            continue
        if term in evaluated and version < first:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{term}:premature(binds-from-{since})")
        elif term not in evaluated and version >= first:
            refusals.append(f"REFUSED:REQ_TERM_UNBOUND:{term}:required-from-{since}")
            evaluated.add(term)
    return tuple(t for t in TERM_REGISTRY if t in evaluated), sorted(refusals)


def theorem(terms: tuple[str, ...]) -> str:
    """``RELEASE = C AND A AND ...`` over the evaluated terms (the six-term string is unchanged)."""
    return "RELEASE = " + " AND ".join(terms)


KINDS = ("AC", "FALSIFIER")
STATES = ("PASS", "BLOCKED", "REFUSED", "UNKNOWN")

FAILURE_CLASSES = (
    "TRANSPORT_FAILURE",
    "BUILD_FAILURE",
    "VERIFICATION_FAILURE",
    "AUTHORITY_FAILURE",
    "EVIDENCE_FAILURE",
    "DEPENDENCY_FAILURE",
    "CAPABILITY_GAP",
    "MODEL_COUNTEREXAMPLE",
    "SUBJECT_FAILURE",
)
BROKEN_TERMS = (
    "mu_on_O",
    "admission_vacuous",
    "mu_unlawful",
    "R_missing_identity",
    "R_missing_authority",
    "R_missing_consequence",
    "R_missing_replay",
    "R_missing_standing",
    "R_not_fed_back",
)

# Requirement-graph admission (requirements.py).
REQ_RULES = (
    "REQ_MALFORMED",
    "REQ_DUPLICATE_ID",
    "REQ_COVERAGE_GAP",
    "REQ_OWNER_UNADMITTED",
    "REQ_TERM_UNBOUND",
    "REQ_PREMISE_UNBOUND",
    "REQ_KIND_UNKNOWN",
)
# Projection (projector.py).
PROJECTOR_RULES = ("PROJECTION_DRIFT", "PROJECTION_INPUT_MISSING")
# Berthier recompile court (berthier.py).
BERTHIER_RULES = (
    "STALE_PROJECTION",
    "ARTIFACT_DIGEST_MISMATCH",
    "OMITTED_SUBJECT",
    "UNEVIDENCED_WORK",
    "AUTHORITY_INCREASE",
    "BREAK_GLASS_AS_NORMAL",
    "PREMISE_UNBOUND",
    "DEPENDENCY_CYCLE",
    "NO_RENEWAL_DELTA",
)
# Crown refusals (crown.py + evidence.py): each one makes the release REFUSED.
CROWN_RULES = (
    "MANIFEST_INVALID",
    "SUBJECT_NOT_TERMINAL",
    "ORIGIN_AUTHORITY_NOT_UNIQUE",
    "ARTIFACT_REFUSED",
    "ARTIFACT_SUBJECT_SPLIT",
    "UNAUTHORIZED_WORKTREE",
    "TRANSIENT_DEPENDENCY",
    "SHA_NOT_MERGED",
    "COLD_RECONSTRUCTION_DIVERGED",
    "BERTHIER_COURT_FAILED",
    "XPROD_REFUSED",
    "TAG_SHA_SPLIT",
    "CLAIM_WITHOUT_RECEIPT",
    "RECEIPT_CHAIN_BROKEN",
    "CROWN_SHA_SPLIT",
    "BLOCKED_WITHOUT_TYPE",
    "UNKNOWN_EVIDENCE_KIND",
    "PRIVATE_OBSERVATION_DIGEST_MISMATCH",
    "PRIVATE_HEAD_SPLIT",
    "REQUIRED_UNKNOWN",
    "VERIFIER_CRASHED",
)
# Post-tag refusals (posttag.py, chain.py): the tag, its recorded subject and the
# historical receipt are immutable; any recomputation that disagrees is REFUSED.
POST_TAG_RULES = (
    "TAG_OBJECT_DIGEST_MISMATCH",
    "TAG_MUTATED",
    "TAG_SUBJECT_SPLIT",
    "TAG_RECEIPT_SPLIT",
    "SUBJECT_TREE_MISMATCH",
    "HISTORICAL_OBSERVATION_SPLIT",
    "PAYLOAD_MUTATED_POST_TAG",
)
# Terminality policy refusals (policy.py + evidence.py owner rule): the per-requirement
# admitted terminal states, their RFC grounding, and the receipt owner.
TERMINALITY_RULES = (
    "TERMINALITY_POLICY_MISSING",
    "POLICY_COVERAGE_GAP",
    "POLICY_RELAXATION_UNGROUNDED",
    "ACCEPTANCE_DRIFT",
    "OWNER_SPLIT",
)
# Evidence-binding refusals (binding.py): every PASS names the exact subject it evaluated,
# the durable container that holds the evidence, the evidence digest and the lineage proof
# between them (RFC-0004 §36 owner, §39 classes; CE23-9 durable locator grammar).
BINDING_RULES = (
    "EVIDENCE_SUBJECT_SPLIT",
    "EVIDENCE_SUBJECT_MUTABLE",
    "EVIDENCE_LINEAGE_MISSING",
    "EVIDENCE_DIGEST_MISMATCH",
    "EVIDENCE_NOT_DURABLE",
    "EVIDENCE_CONTAINER_CLAIMS_SUBJECT",
    "EVIDENCE_DELTA_MISCLAIMED",
)
# Evidence-binding typed blocker: the subject->container delta holds non-receipt paths, so
# the producer subject's standing is not inherited by the container head.
BINDING_BLOCKERS = ("EVIDENCE_DELTA_UNBOUNDED",)
BINDING_KINDS = ("IN_TREE_DERIVED", "REMOTE_RECEIPT", "OPERATOR_LOCAL", "LOCAL_RECEIPT")
SCHEMA_BINDING = "https://chatman.dev/root-crown/evidence-binding/v1"
# Post-tag typed blockers (lawful, non-ALIVE).
# CURRENT_HEAD_UNATTESTED: the observed root head is not the attested head, so the current
# conformance section describes a head nobody observed (never affects historical standing).
POST_TAG_BLOCKERS = ("TAG_UNRECORDED", "REPLAY_DIVERGED", "SUBJECT_ABSENT", "CURRENT_HEAD_UNATTESTED")
# RECEIPT_CHAIN_BROKEN detail tokens (chain.py).
CHAIN_TOKENS = ("PARENT_DIGEST", "PARENT_REFUSED", "PARENT_UNTYPED_BLOCKED", "PARENT_NOT_ANCESTOR")
# Typed blockers: lawful, terminal, non-ALIVE.
BLOCKER_CODES = (
    "EVIDENCE_ABSENT",
    "OBSERVATION_MISSING",
    "OBSERVATION_STALE",
    "NOT_COLD",
    "CLOSURE_PARTIAL",
    "ARTIFACT_BLOCKED",
    "ARTIFACT_UNBOUND",
    "ARTIFACT_NOT_JSON",
    "XPROD_BLOCKED",
    "CROWN_DEPENDENCIES_OPEN",
    "NEW_HEAD_UNEVIDENCED",
)
# Term U (RFC-0005) composition: the autonomic_crown receipt the premise binds U to.
# AUTONOMIC_RECEIPT_DIGEST_MISMATCH: the receipt's schema or receipt_digest does not recompute.
AUTONOMIC_RULES = ("AUTONOMIC_RECEIPT_DIGEST_MISMATCH",)
# Typed blockers: the receipt is for another release line (stale), or it recomputes but
# does not witness U (execution not ALIVE or autonomy not AUTONOMIC).
AUTONOMIC_BLOCKERS = ("AUTONOMIC_RECEIPT_STALE", "AUTONOMIC_NOT_AUTONOMIC")
# Tag decision reasons (tag.py).
TAG_RULES = ("CROWN_NOT_ALIVE", "SHA_MISMATCH", "TAG_EXISTS_ELSEWHERE", "RECEIPT_UNVERIFIED")

RULES = CROWN_RULES

FAILURE_CLASS: dict[str, tuple[str, str]] = {
    # requirements graph
    "REQ_MALFORMED": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "REQ_DUPLICATE_ID": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "REQ_COVERAGE_GAP": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "REQ_OWNER_UNADMITTED": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "REQ_TERM_UNBOUND": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "REQ_PREMISE_UNBOUND": ("AUTHORITY_FAILURE", "mu_on_O"),
    "REQ_KIND_UNKNOWN": ("CAPABILITY_GAP", "admission_vacuous"),
    # projector
    "PROJECTION_DRIFT": ("VERIFICATION_FAILURE", "mu_unlawful"),
    "PROJECTION_INPUT_MISSING": ("EVIDENCE_FAILURE", "R_missing_replay"),
    # berthier
    "STALE_PROJECTION": ("DEPENDENCY_FAILURE", "R_not_fed_back"),
    "ARTIFACT_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "OMITTED_SUBJECT": ("DEPENDENCY_FAILURE", "R_missing_consequence"),
    "UNEVIDENCED_WORK": ("EVIDENCE_FAILURE", "mu_on_O"),
    "AUTHORITY_INCREASE": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "BREAK_GLASS_AS_NORMAL": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "PREMISE_UNBOUND": ("AUTHORITY_FAILURE", "mu_on_O"),
    "DEPENDENCY_CYCLE": ("DEPENDENCY_FAILURE", "mu_unlawful"),
    "NO_RENEWAL_DELTA": ("VERIFICATION_FAILURE", "admission_vacuous"),
    # crown refusals
    "MANIFEST_INVALID": ("VERIFICATION_FAILURE", "mu_unlawful"),
    "SUBJECT_NOT_TERMINAL": ("SUBJECT_FAILURE", "R_missing_standing"),
    "ORIGIN_AUTHORITY_NOT_UNIQUE": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "ARTIFACT_REFUSED": ("VERIFICATION_FAILURE", "R_missing_standing"),
    "ARTIFACT_SUBJECT_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "UNAUTHORIZED_WORKTREE": ("SUBJECT_FAILURE", "mu_on_O"),
    "TRANSIENT_DEPENDENCY": ("DEPENDENCY_FAILURE", "R_missing_identity"),
    "SHA_NOT_MERGED": ("SUBJECT_FAILURE", "R_missing_identity"),
    "COLD_RECONSTRUCTION_DIVERGED": ("BUILD_FAILURE", "R_missing_replay"),
    "BERTHIER_COURT_FAILED": ("VERIFICATION_FAILURE", "mu_unlawful"),
    "XPROD_REFUSED": ("MODEL_COUNTEREXAMPLE", "admission_vacuous"),
    "TAG_SHA_SPLIT": ("AUTHORITY_FAILURE", "R_missing_identity"),
    "CLAIM_WITHOUT_RECEIPT": ("EVIDENCE_FAILURE", "R_missing_consequence"),
    "RECEIPT_CHAIN_BROKEN": ("EVIDENCE_FAILURE", "R_not_fed_back"),
    "CROWN_SHA_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "BLOCKED_WITHOUT_TYPE": ("EVIDENCE_FAILURE", "R_missing_standing"),
    "UNKNOWN_EVIDENCE_KIND": ("CAPABILITY_GAP", "admission_vacuous"),
    "PRIVATE_OBSERVATION_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "PRIVATE_HEAD_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "REQUIRED_UNKNOWN": ("EVIDENCE_FAILURE", "R_missing_standing"),
    "VERIFIER_CRASHED": ("VERIFICATION_FAILURE", "mu_unlawful"),
    # post-tag refusals
    "TAG_OBJECT_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "TAG_MUTATED": ("AUTHORITY_FAILURE", "R_missing_identity"),
    "TAG_SUBJECT_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "TAG_RECEIPT_SPLIT": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "SUBJECT_TREE_MISMATCH": ("SUBJECT_FAILURE", "R_missing_replay"),
    "HISTORICAL_OBSERVATION_SPLIT": ("EVIDENCE_FAILURE", "mu_on_O"),
    "PAYLOAD_MUTATED_POST_TAG": ("SUBJECT_FAILURE", "mu_unlawful"),
    # terminality policy
    "TERMINALITY_POLICY_MISSING": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "POLICY_COVERAGE_GAP": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "POLICY_RELAXATION_UNGROUNDED": ("AUTHORITY_FAILURE", "mu_on_O"),
    "ACCEPTANCE_DRIFT": ("VERIFICATION_FAILURE", "R_not_fed_back"),
    "OWNER_SPLIT": ("AUTHORITY_FAILURE", "R_missing_authority"),
    # evidence binding
    "EVIDENCE_SUBJECT_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "EVIDENCE_SUBJECT_MUTABLE": ("SUBJECT_FAILURE", "R_missing_identity"),
    "EVIDENCE_LINEAGE_MISSING": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "EVIDENCE_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "EVIDENCE_NOT_DURABLE": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "EVIDENCE_CONTAINER_CLAIMS_SUBJECT": ("SUBJECT_FAILURE", "mu_on_O"),
    "EVIDENCE_DELTA_MISCLAIMED": ("EVIDENCE_FAILURE", "admission_vacuous"),
    "EVIDENCE_DELTA_UNBOUNDED": ("EVIDENCE_FAILURE", "R_missing_identity"),
    # post-tag typed blockers
    "TAG_UNRECORDED": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "REPLAY_DIVERGED": ("VERIFICATION_FAILURE", "R_missing_replay"),
    "SUBJECT_ABSENT": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "CURRENT_HEAD_UNATTESTED": ("SUBJECT_FAILURE", "R_missing_identity"),
    # typed blockers
    "EVIDENCE_ABSENT": ("EVIDENCE_FAILURE", "R_missing_consequence"),
    "OBSERVATION_MISSING": ("TRANSPORT_FAILURE", "R_missing_identity"),
    "OBSERVATION_STALE": ("EVIDENCE_FAILURE", "R_not_fed_back"),
    "NOT_COLD": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "CLOSURE_PARTIAL": ("DEPENDENCY_FAILURE", "R_missing_standing"),
    "ARTIFACT_BLOCKED": ("DEPENDENCY_FAILURE", "R_missing_standing"),
    "ARTIFACT_UNBOUND": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "ARTIFACT_NOT_JSON": ("EVIDENCE_FAILURE", "R_missing_consequence"),
    "XPROD_BLOCKED": ("EVIDENCE_FAILURE", "R_missing_standing"),
    "CROWN_DEPENDENCIES_OPEN": ("DEPENDENCY_FAILURE", "R_missing_standing"),
    "NEW_HEAD_UNEVIDENCED": ("EVIDENCE_FAILURE", "R_missing_identity"),
    # term U (autonomic receipt composition)
    "AUTONOMIC_RECEIPT_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "AUTONOMIC_RECEIPT_STALE": ("EVIDENCE_FAILURE", "R_not_fed_back"),
    "AUTONOMIC_NOT_AUTONOMIC": ("CAPABILITY_GAP", "mu_on_O"),
    # tag
    "CROWN_NOT_ALIVE": ("DEPENDENCY_FAILURE", "R_missing_standing"),
    "SHA_MISMATCH": ("SUBJECT_FAILURE", "R_missing_identity"),
    "TAG_EXISTS_ELSEWHERE": ("AUTHORITY_FAILURE", "R_missing_identity"),
    "RECEIPT_UNVERIFIED": ("EVIDENCE_FAILURE", "R_missing_identity"),
}

ALL_CODES = (
    REQ_RULES
    + PROJECTOR_RULES
    + BERTHIER_RULES
    + CROWN_RULES
    + POST_TAG_RULES
    + TERMINALITY_RULES
    + BINDING_RULES
    + BINDING_BLOCKERS
    + POST_TAG_BLOCKERS
    + BLOCKER_CODES
    + AUTONOMIC_RULES
    + AUTONOMIC_BLOCKERS
    + TAG_RULES
)


@dataclass(frozen=True, slots=True)
class Requirement:
    id: str
    kind: str
    term: str
    owner_repo: str
    acceptance: str
    evidence_kind: str
    evidence_locator: str
    premise_refs: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    required: bool = True

    def row(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "term": self.term,
            "owner_repo": self.owner_repo,
            "acceptance": self.acceptance,
            "evidence_kind": self.evidence_kind,
            "evidence_locator": self.evidence_locator,
            "premise_refs": list(self.premise_refs),
            "depends_on": list(self.depends_on),
            "required": self.required,
        }

    @property
    def locator_repo(self) -> str | None:
        """Repository a remote locator names (``owner/name:path``), else None (local)."""
        if self.evidence_locator.startswith("local:"):
            return None
        head, sep, _ = self.evidence_locator.partition(":")
        return head if sep and "/" in head else None


@dataclass(frozen=True, slots=True)
class EvidenceBinding:
    """What a PASS evaluated, where its evidence durably lives, and why the two are one lineage.

    ``evaluated_subject_sha`` is the commit the evidence speaks about (the producer subject);
    ``evidence_container_sha`` is the commit that holds the evidence bytes. They coincide only
    for IN_TREE_DERIVED evidence (derived by the crown from its own tree). Otherwise
    ``lineage_proof`` carries the observed compare status and the changed paths between them,
    classified by ``binding.classify_delta``. ``binding_digest`` is the canonical digest of
    every other field (recomputed by ``binding.admit``).
    """

    requirement_id: str
    kind: str
    evaluated_subject_sha: str | None
    evaluated_subject_kind: str
    container_repository: str | None
    evidence_container_sha: str | None
    evidence_locator: str | None
    evidence_digest: str | None
    producer: str
    court: str
    command: str | None
    exit_code: int | None
    toolchain: str | None
    standing: str | None
    owner: str | None
    owner_source: str
    lineage_proof: dict[str, Any]
    binding_digest: str = ""

    def body(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_BINDING,
            "requirement_id": self.requirement_id,
            "kind": self.kind,
            "evaluated_subject_sha": self.evaluated_subject_sha,
            "evaluated_subject_kind": self.evaluated_subject_kind,
            "container_repository": self.container_repository,
            "evidence_container_sha": self.evidence_container_sha,
            "evidence_locator": self.evidence_locator,
            "evidence_digest": self.evidence_digest,
            "producer": self.producer,
            "court": self.court,
            "command": self.command,
            "exit_code": self.exit_code,
            "toolchain": self.toolchain,
            "standing": self.standing,
            "owner": self.owner,
            "owner_source": self.owner_source,
            "lineage_proof": {
                "status": self.lineage_proof.get("status"),
                "delta_paths": None
                if self.lineage_proof.get("delta_paths") is None
                else sorted(self.lineage_proof["delta_paths"]),
                "delta_class": self.lineage_proof.get("delta_class"),
            },
        }

    def computed_digest(self) -> str:
        return canonical_digest(self.body())

    def sealed(self) -> "EvidenceBinding":
        """This binding with ``binding_digest`` set to the digest of its body."""
        from dataclasses import replace

        return replace(self, binding_digest=self.computed_digest())

    def as_dict(self) -> dict[str, Any]:
        return self.body() | {"binding_digest": self.binding_digest}


@dataclass(frozen=True, slots=True)
class ReqState:
    state: str
    code: str | None = None
    detail: str = ""
    subject_sha: str | None = None
    failure_class: str | None = field(default=None)
    broken_term: str | None = field(default=None)
    binding: EvidenceBinding | None = field(default=None)

    def __post_init__(self) -> None:
        if self.code is not None and self.failure_class is None and self.code in FAILURE_CLASS:
            cls, term = FAILURE_CLASS[self.code]
            object.__setattr__(self, "failure_class", cls)
            object.__setattr__(self, "broken_term", term)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "code": self.code,
            "failure_class": self.failure_class,
            "broken_term": self.broken_term,
            "detail": self.detail,
            "subject_sha": self.subject_sha,
            # v2 requirement state: the evidence binding (None for non-PASS states).
            "binding": None if self.binding is None else self.binding.as_dict(),
        }


def PASS(detail: str = "", subject_sha: str | None = None, binding: EvidenceBinding | None = None) -> ReqState:
    return ReqState("PASS", None, detail, subject_sha, binding=binding)


def BLOCKED(code: str, detail: str = "", subject_sha: str | None = None) -> ReqState:
    return ReqState("BLOCKED", code, detail, subject_sha)


def REFUSED(code: str, detail: str = "", subject_sha: str | None = None) -> ReqState:
    return ReqState("REFUSED", code, detail, subject_sha)


def UNKNOWN(code: str, detail: str = "", subject_sha: str | None = None) -> ReqState:
    return ReqState("UNKNOWN", code, detail, subject_sha)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: object) -> str:
    return canonical_digest(value)


def code_of(refusal: str) -> str:
    """``REFUSED:<CODE>:...`` or ``BLOCKED:<CODE>:...`` -> ``<CODE>``."""
    parts = refusal.split(":")
    return parts[1] if len(parts) > 1 else parts[0]
