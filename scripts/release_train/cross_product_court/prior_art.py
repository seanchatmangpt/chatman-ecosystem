from __future__ import annotations

import hashlib
import itertools
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import Enum

_SHA40_SUBJECT = re.compile(r"^[^/\s]+/[^@\s]+@[0-9a-f]{40}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class PriorArtDecision(str, Enum):
    REUSE = "REUSE"
    COMPOSE = "COMPOSE"
    EXTEND = "EXTEND"
    INVENT = "INVENT"
    REFUSED = "REFUSED"


@dataclass(frozen=True, slots=True)
class PriorArtCandidate:
    candidate_id: str
    exact_subject: str
    semantic_contract_digest: str
    qualification_receipt_digest: str
    covers: tuple[str, ...]
    gap_falsifier_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must be non-empty")
        if not _SHA40_SUBJECT.fullmatch(self.exact_subject):
            raise ValueError("exact_subject must be owner/repo@40hex")
        for name, value in (
            ("semantic_contract_digest", self.semantic_contract_digest),
            ("qualification_receipt_digest", self.qualification_receipt_digest),
        ):
            if not _SHA256.fullmatch(value):
                raise ValueError(f"{name} must be sha256:<64-hex>")
        if self.gap_falsifier_digest is not None and not _SHA256.fullmatch(
            self.gap_falsifier_digest
        ):
            raise ValueError("gap_falsifier_digest must be sha256:<64-hex>")
        if any(not item.strip() for item in self.covers):
            raise ValueError("covers must contain non-empty semantic ids")
        if len(self.covers) != len(set(self.covers)):
            raise ValueError("covers must be unique")


@dataclass(frozen=True, slots=True)
class PriorArtDecisionCase:
    case_id: str
    required_semantics: tuple[str, ...]
    candidates: tuple[PriorArtCandidate, ...]
    residual_falsifier_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be non-empty")
        if not self.required_semantics:
            raise ValueError("required_semantics must be non-empty")
        if any(not item.strip() for item in self.required_semantics):
            raise ValueError("required_semantics must contain non-empty ids")
        if len(self.required_semantics) != len(set(self.required_semantics)):
            raise ValueError("required_semantics must be unique")
        ids = tuple(item.candidate_id for item in self.candidates)
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")
        subjects = tuple(item.exact_subject for item in self.candidates)
        if len(subjects) != len(set(subjects)):
            raise ValueError("candidate exact subjects must be unique")
        if self.residual_falsifier_digest is not None and not _SHA256.fullmatch(
            self.residual_falsifier_digest
        ):
            raise ValueError("residual_falsifier_digest must be sha256:<64-hex>")


@dataclass(frozen=True, slots=True)
class PriorArtDecisionReceipt:
    schema: str
    case_id: str
    decision: PriorArtDecision
    required_semantics: tuple[str, ...]
    selected_candidate_ids: tuple[str, ...]
    selected_subjects: tuple[str, ...]
    covered_semantics: tuple[str, ...]
    residual_semantics: tuple[str, ...]
    falsifier_digest: str | None
    authority: str
    refusals: tuple[str, ...]
    receipt_digest: str

    def canonical_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("receipt_digest", None)
        payload["decision"] = self.decision.value
        return payload


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _minimal_cover(
    required: set[str], candidates: tuple[PriorArtCandidate, ...]
) -> tuple[PriorArtCandidate, ...] | None:
    ordered = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    for size in range(1, len(ordered) + 1):
        for combo in itertools.combinations(ordered, size):
            covered = set().union(*(set(item.covers) for item in combo))
            if required <= covered:
                return combo
    return None


def evaluate_prior_art(case: PriorArtDecisionCase) -> PriorArtDecisionReceipt:
    required = set(case.required_semantics)
    refusals: list[str] = []

    if not case.candidates:
        refusals.append("REFUSED:PRIOR_ART_SEARCH_MISSING")
        decision = PriorArtDecision.REFUSED
        selected: tuple[PriorArtCandidate, ...] = ()
        covered: set[str] = set()
        residual = required
        falsifier = None
    else:
        full = tuple(
            sorted(
                (
                    candidate
                    for candidate in case.candidates
                    if required <= set(candidate.covers)
                ),
                key=lambda item: item.candidate_id,
            )
        )

        if full:
            decision = PriorArtDecision.REUSE
            selected = (full[0],)
            covered = required
            residual = set()
            falsifier = None
        else:
            composition = _minimal_cover(required, case.candidates)
            if composition is not None:
                decision = PriorArtDecision.COMPOSE
                selected = composition
                covered = required
                residual = set()
                falsifier = None
            else:
                all_covered = set().union(
                    *(set(item.covers) for item in case.candidates)
                )
                covered = required & all_covered
                residual = required - covered
                selected = tuple(
                    sorted(
                        (
                            item
                            for item in case.candidates
                            if required & set(item.covers)
                        ),
                        key=lambda item: item.candidate_id,
                    )
                )

                if covered:
                    if case.residual_falsifier_digest is None:
                        decision = PriorArtDecision.REFUSED
                        refusals.append("REFUSED:EXTEND_RESIDUAL_UNFALSIFIED")
                        falsifier = None
                    else:
                        decision = PriorArtDecision.EXTEND
                        falsifier = case.residual_falsifier_digest
                else:
                    all_gaps_falsified = all(
                        item.gap_falsifier_digest is not None
                        for item in case.candidates
                    )
                    if (
                        case.residual_falsifier_digest is None
                        or not all_gaps_falsified
                    ):
                        decision = PriorArtDecision.REFUSED
                        refusals.append("REFUSED:INVENT_WITHOUT_PRIOR_ART_FALSIFIER")
                        falsifier = None
                    else:
                        decision = PriorArtDecision.INVENT
                        selected = ()
                        falsifier = case.residual_falsifier_digest

    receipt = PriorArtDecisionReceipt(
        schema="https://chatman.dev/prior-art-decision/receipt/v1",
        case_id=case.case_id,
        decision=decision,
        required_semantics=tuple(sorted(required)),
        selected_candidate_ids=tuple(item.candidate_id for item in selected),
        selected_subjects=tuple(item.exact_subject for item in selected),
        covered_semantics=tuple(sorted(covered)),
        residual_semantics=tuple(sorted(residual)),
        falsifier_digest=falsifier,
        authority="NONE",
        refusals=tuple(sorted(set(refusals))),
        receipt_digest="sha256:" + "0" * 64,
    )
    return replace(
        receipt,
        receipt_digest=_digest(receipt.canonical_payload()),
    )
