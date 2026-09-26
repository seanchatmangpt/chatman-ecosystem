"""Autonomic crown data model (RFC-0005: term U, three orthogonal standings, U-01..U-18).

Every code the autonomic crown can emit is listed in ``CODES`` with its RFC-0004 §39
failure class and its Chatman-equation ``broken_term``; a test asserts the table is total
over every emitted code. ``SEVERITY`` splits codes into integrity refusals (the court
refuses its own inputs: exit 2) and typed blockers (lawful NOT_AUTONOMIC: exit 3).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from scripts.release_train.root_crown.model import BROKEN_TERMS, FAILURE_CLASSES

SCHEMA_RECEIPT = "https://chatman.dev/autonomic-crown/receipt/v1"
SCHEMA_EDGES = "edges.v1"
SCHEMA_GATES = "https://chatman.dev/autonomic-crown/gates/v1"
PREMISE_SET = ("RFC-0004", "RFC-0005")
ROOT_REPOSITORY = "seanchatmangpt/chatman-ecosystem"

GATE_IDS = tuple(f"U-{n:02d}" for n in range(1, 19))
STAGES = ("start", "observe", "admit", "decompose", "construct", "actuate", "verify", "repair", "replay", "continue")
OWNER_KINDS = ("machine", "human", "llm")
EVIDENCE_KINDS = ("receipt", "run", "log", "workflow", "policy")
# Evidence kinds that can witness machine ownership: a trigger or a machine-written record.
MACHINE_WITNESS_KINDS = ("receipt", "run", "workflow")

EXECUTION = ("ALIVE", "PARTIAL_ALIVE", "BLOCKED", "UNSUPPORTED", "REFUSED", "UNKNOWN")
AUTONOMY = ("AUTONOMIC", "NOT_AUTONOMIC", "UNKNOWN")
AUTHORITY = ("AUTHORIZED", "WAITING_EXTERNAL_AUTHORITY", "REFUSED")
GATE_STATES = ("PASS", "BLOCKED", "REFUSED")

# RFC-0005 §8: variant -> recoverability (R recoverable, U unrecoverable). Fixed; never reclassified.
RECOVERABILITY: dict[tuple[str, str], str] = {
    ("TRANSPORT_FAILURE", "any"): "R",
    ("BUILD_FAILURE", "any"): "R",
    ("VERIFICATION_FAILURE", "transient"): "R",
    ("VERIFICATION_FAILURE", "deterministic"): "U",
    ("AUTHORITY_FAILURE", "any"): "U",
    ("EVIDENCE_FAILURE", "stale"): "R",
    ("EVIDENCE_FAILURE", "forged chain"): "U",
    ("DEPENDENCY_FAILURE", "local NEW_HEAD"): "R",
    ("DEPENDENCY_FAILURE", "remote producer"): "U",
    ("CAPABILITY_GAP", "any"): "U",
    ("MODEL_COUNTEREXAMPLE", "any"): "U",
    ("SUBJECT_FAILURE", "crown-sha split"): "R",
}

# code -> (RFC-0004 §39 failure class, broken_term)
CODES: dict[str, tuple[str, str]] = {
    # integrity refusals over the court's own inputs (exit 2)
    "GATE_COVERAGE_GAP": ("BUILD_FAILURE", "mu_on_O"),
    "EDGE_MALFORMED": ("VERIFICATION_FAILURE", "R_missing_identity"),
    "STAGE_UNCOVERED": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "OWNER_KIND_UNWITNESSED": ("EVIDENCE_FAILURE", "R_missing_standing"),
    "LOCATOR_NOT_DURABLE": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "EVIDENCE_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "AUTHORITY_AMPLIFICATION": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "RECEIPT_UNVERIFIED": ("VERIFICATION_FAILURE", "R_missing_identity"),
    "CHAIN_FORGED": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "IMPORT_DIGEST_MISMATCH": ("EVIDENCE_FAILURE", "R_missing_identity"),
    "GATE_PASS_WITHOUT_EVIDENCE": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "AUTONOMY_WITHOUT_ALIVE": ("VERIFICATION_FAILURE", "R_missing_standing"),
    "ILLEGAL_STANDING_COMBINATION": ("VERIFICATION_FAILURE", "R_missing_standing"),
    "UNCHANGED_RETRY": ("VERIFICATION_FAILURE", "R_not_fed_back"),
    "MODEL_COUNTEREXAMPLE": ("MODEL_COUNTEREXAMPLE", "mu_unlawful"),
    "PREMISE_SET_REFUSED": ("VERIFICATION_FAILURE", "mu_on_O"),
    # typed blockers (exit 3): §8 fault responses
    "TRANSPORT_UNAVAILABLE": ("TRANSPORT_FAILURE", "R_missing_replay"),
    "EVIDENCE_UNRESOLVED": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "UNSUPPORTED_EVIDENCE_KIND": ("CAPABILITY_GAP", "R_missing_replay"),
    "SUBJECT_SPLIT": ("SUBJECT_FAILURE", "R_missing_identity"),
    "NEW_HEAD": ("DEPENDENCY_FAILURE", "R_missing_identity"),
    "WAITING_PRODUCER": ("DEPENDENCY_FAILURE", "R_not_fed_back"),
    # typed blockers (exit 3): gate measurements below threshold (RFC-0005 §7, §12)
    "HUMAN_OR_LLM_EDGE": ("CAPABILITY_GAP", "mu_on_O"),
    "HUMAN_OPERATIONAL_DEPENDENCY": ("CAPABILITY_GAP", "mu_on_O"),
    "GENERAL_LLM_ON_RECURRING_PATH": ("CAPABILITY_GAP", "mu_on_O"),
    "EVIDENCE_NOT_EXACT": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "FAULT_UNREPAIRED": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "FAULT_UNCONTAINED": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "MUTANT_SURVIVED": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "AUTHORITY_CONFIGURATION": ("AUTHORITY_FAILURE", "R_missing_authority"),
    "UNMEASURED": ("EVIDENCE_FAILURE", "R_missing_consequence"),
    "NON_DURABLE_RECEIPT_STORE": ("EVIDENCE_FAILURE", "R_missing_replay"),
    "PREMISE_SET_FAILED": ("VERIFICATION_FAILURE", "mu_on_O"),
    "UNPINNED_TOOLCHAIN": ("DEPENDENCY_FAILURE", "R_missing_identity"),
    "HIDDEN_LOCAL_STATE": ("EVIDENCE_FAILURE", "mu_on_O"),
    "BLOCKED_ONLY_WARNS": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "INTERNAL_SUBJECT_NOT_AUTONOMIC": ("DEPENDENCY_FAILURE", "R_not_fed_back"),
    "SINGLE_SCHEDULER": ("DEPENDENCY_FAILURE", "R_not_fed_back"),
    "INSUFFICIENT_CLEAN_CYCLES": ("VERIFICATION_FAILURE", "R_not_fed_back"),
}
INTEGRITY = frozenset(
    {
        "GATE_COVERAGE_GAP",
        "EDGE_MALFORMED",
        "STAGE_UNCOVERED",
        "OWNER_KIND_UNWITNESSED",
        "LOCATOR_NOT_DURABLE",
        "EVIDENCE_DIGEST_MISMATCH",
        "AUTHORITY_AMPLIFICATION",
        "RECEIPT_UNVERIFIED",
        "CHAIN_FORGED",
        "IMPORT_DIGEST_MISMATCH",
        "GATE_PASS_WITHOUT_EVIDENCE",
        "AUTONOMY_WITHOUT_ALIVE",
        "ILLEGAL_STANDING_COMBINATION",
        "UNCHANGED_RETRY",
        "MODEL_COUNTEREXAMPLE",
        "PREMISE_SET_REFUSED",
    }
)

assert all(cls in FAILURE_CLASSES and term in BROKEN_TERMS for cls, term in CODES.values())


@dataclass(frozen=True, slots=True)
class Finding:
    """One typed finding: ``REFUSED:<code>:<subject>`` (integrity) or ``BLOCKED:<code>:<subject>``."""

    code: str
    subject: str
    detail: str = ""

    @property
    def severity(self) -> str:
        return "REFUSED" if self.code in INTEGRITY else "BLOCKED"

    def as_dict(self) -> dict[str, str]:
        cls, term = CODES[self.code]
        return {
            "code": self.code,
            "severity": self.severity,
            "subject": self.subject,
            "failure_class": cls,
            "broken_term": term,
            "detail": self.detail,
        }

    def __str__(self) -> str:
        return f"{self.severity}:{self.code}:{self.subject}"


@dataclass(slots=True)
class GateResult:
    id: str
    state: str
    measured: Any
    threshold: str
    code: str | None = None
    detail: str = ""
    evidence: dict[str, str] | None = None
    findings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "state": self.state,
            "measured": self.measured,
            "threshold": self.threshold,
            "detail": self.detail,
            "evidence": self.evidence,
            "findings": sorted(self.findings),
        }
        if self.code is not None:
            cls, term = CODES[self.code]
            out.update({"code": self.code, "failure_class": cls, "broken_term": term})
        return out


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: Any) -> str:
    return "sha256:" + sha256_bytes(canonical(value))


def pretty(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
