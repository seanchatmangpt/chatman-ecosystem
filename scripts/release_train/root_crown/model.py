"""Root crown data model: requirements, requirement states, rule table.

RFC-0004 (engineering-standards@7e8d4c5c) §3: RELEASE = C ∧ A ∧ R ∧ X ∧ F ∧ M.
Every refusal/blocker code the root crown can emit is listed in ``FAILURE_CLASS``
with its RFC §39 class and its Chatman-equation ``broken_term``; a test asserts
the table is total over every emitted code.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from scripts.release_train.cross_product_court.model import canonical_digest

SCHEMA_RECEIPT = "https://chatman.dev/root-crown/receipt/v1"
SCHEMA_OBSERVATIONS = "https://chatman.dev/root-crown/observations/v1"

TERMS = ("C", "A", "R", "X", "F", "M")
TERM_NAMES = {
    "C": "closure",
    "A": "authority integrity",
    "R": "receipts and replay",
    "X": "semantic cross-product verification",
    "F": "formalized recurring reasoning",
    "M": "migration and repository integrity",
}
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
)
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
    # tag
    "CROWN_NOT_ALIVE": ("DEPENDENCY_FAILURE", "R_missing_standing"),
    "SHA_MISMATCH": ("SUBJECT_FAILURE", "R_missing_identity"),
    "TAG_EXISTS_ELSEWHERE": ("AUTHORITY_FAILURE", "R_missing_identity"),
    "RECEIPT_UNVERIFIED": ("EVIDENCE_FAILURE", "R_missing_identity"),
}

ALL_CODES = REQ_RULES + PROJECTOR_RULES + BERTHIER_RULES + CROWN_RULES + BLOCKER_CODES + TAG_RULES


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
class ReqState:
    state: str
    code: str | None = None
    detail: str = ""
    subject_sha: str | None = None
    failure_class: str | None = field(default=None)
    broken_term: str | None = field(default=None)

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
        }


def PASS(detail: str = "", subject_sha: str | None = None) -> ReqState:
    return ReqState("PASS", None, detail, subject_sha)


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
