from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class Formalism(str, Enum):
    HDDL = "HDDL"
    FOND = "FOND"
    TLA = "TLA+"
    POWL = "POWL"
    OCEL = "OCEL2"
    BRCE = "BRCE"
    RECEIPT = "RECEIPT"


class EvidenceResult(str, Enum):
    PASS = "PASS"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    REFUSED = "REFUSED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class Standing(str, Enum):
    ALIVE = "ALIVE"
    PARTIAL_ALIVE = "PARTIAL_ALIVE"
    BLOCKED = "BLOCKED"
    REFUSED = "REFUSED"


@dataclass(frozen=True, slots=True)
class SubjectBinding:
    repository: str
    subject_sha: str

    def __post_init__(self) -> None:
        if "/" not in self.repository or self.repository.startswith("/"):
            raise ValueError("repository must be owner/name")
        if not _SHA40.fullmatch(self.subject_sha):
            raise ValueError("subject_sha must be exact 40-hex identity")

    @property
    def identity(self) -> str:
        return f"{self.repository}@{self.subject_sha}"


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    repository: str
    subject_sha: str
    formalism: Formalism
    claim_id: str
    artifact_digest: str
    validator: str
    validator_digest: str
    result: EvidenceResult
    authority: str = "NONE"
    counterexample_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        SubjectBinding(self.repository, self.subject_sha)
        if not self.claim_id.strip():
            raise ValueError("claim_id must be non-empty")
        if not _SHA256.fullmatch(self.artifact_digest):
            raise ValueError("artifact_digest must be sha256:<64-hex>")
        if not self.validator.strip():
            raise ValueError("validator must be non-empty")
        if not _SHA256.fullmatch(self.validator_digest):
            raise ValueError("validator_digest must be sha256:<64-hex>")
        if self.authority != "NONE":
            raise ValueError("cross-product evidence projections carry no authority")
        if self.result is EvidenceResult.COUNTEREXAMPLE:
            if self.counterexample_digest is None or not _SHA256.fullmatch(
                self.counterexample_digest
            ):
                raise ValueError("COUNTEREXAMPLE requires counterexample_digest")
        elif self.counterexample_digest is not None:
            raise ValueError(
                "counterexample_digest is valid only for COUNTEREXAMPLE evidence"
            )

    @property
    def subject_identity(self) -> str:
        return f"{self.repository}@{self.subject_sha}"


@dataclass(frozen=True, slots=True)
class RelationRequirement:
    relation_id: str
    left: Formalism
    right: Formalism
    claim_id: str

    def __post_init__(self) -> None:
        if not self.relation_id.strip():
            raise ValueError("relation_id must be non-empty")
        if not self.claim_id.strip():
            raise ValueError("relation claim_id must be non-empty")
        if self.left == self.right:
            raise ValueError(
                "cross-product relation must span two distinct dimensions"
            )


@dataclass(frozen=True, slots=True)
class MutantExpectation:
    mutant_id: str
    formalism: Formalism
    claim_id: str
    expected: EvidenceResult

    def __post_init__(self) -> None:
        if not self.mutant_id.strip():
            raise ValueError("mutant_id must be non-empty")
        if not self.claim_id.strip():
            raise ValueError("mutant claim_id must be non-empty")
        if self.expected not in {
            EvidenceResult.COUNTEREXAMPLE,
            EvidenceResult.REFUSED,
        }:
            raise ValueError("mutant expectation must fail closed")


@dataclass(frozen=True, slots=True)
class CrossProductCase:
    case_id: str
    semantic_subject_id: str
    subjects: tuple[SubjectBinding, ...]
    required_formalisms: tuple[Formalism, ...]
    evidence: tuple[EvidenceRecord, ...]
    relations: tuple[RelationRequirement, ...]
    mutants: tuple[MutantExpectation, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        if not self.semantic_subject_id.strip():
            raise ValueError("semantic_subject_id must be non-empty")
        if not self.subjects:
            raise ValueError("subjects must be non-empty")
        identities = tuple(item.identity for item in self.subjects)
        if len(identities) != len(set(identities)):
            raise ValueError("subjects must be unique exact identities")
        repositories = tuple(item.repository for item in self.subjects)
        if len(repositories) != len(set(repositories)):
            raise ValueError("one exact subject per repository is allowed in a case")
        if not self.required_formalisms:
            raise ValueError("required_formalisms must be non-empty")
        if len(self.required_formalisms) != len(set(self.required_formalisms)):
            raise ValueError("required_formalisms must be unique")


@dataclass(frozen=True, slots=True)
class CrossProductReceipt:
    schema: str
    case_id: str
    semantic_subject_id: str
    subject_bindings: tuple[str, ...]
    standing: Standing
    claim_ceiling: str
    authority: str
    dimensions_present: tuple[str, ...]
    relations_checked: tuple[str, ...]
    mutants_checked: tuple[str, ...]
    refusals: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    receipt_digest: str

    def canonical_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_digest", None)
        payload["standing"] = self.standing.value
        return payload


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256_text(payload)


def formalism_names(values: Iterable[Formalism]) -> tuple[str, ...]:
    return tuple(sorted(value.value for value in values))
