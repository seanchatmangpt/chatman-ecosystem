from __future__ import annotations

from dataclasses import dataclass

from .admission import SubjectAdmission, admit_subject
from .authority import AuthorityContext
from .claims import EvidenceClaim
from .dependency import DependencyEdge, dependency_order
from .lineage import EvidenceEdge, order_evidence
from .model import ExactSubject, Refused
from .obligations import ObligationProfile
from .plan import PlanStep, build_plan
from .provenance import EvidenceRecord
from .receipt import PromotionReceipt, manufacture_receipt, replay
from .reconcile import reconcile_repo
from .window import ObservationWindow


@dataclass(frozen=True)
class PromotionResult:
    ordered_subjects: tuple[str, ...]
    admissions: tuple[SubjectAdmission, ...]
    steps: tuple[PlanStep, ...]
    receipt: PromotionReceipt


def manufacture(*, predecessor_sha: str, window: ObservationWindow, records: list[EvidenceRecord], evidence_edges: list[EvidenceEdge], claims: list[EvidenceClaim], subjects: list[ExactSubject], dependencies: list[DependencyEdge], authority: AuthorityContext) -> PromotionResult:
    if len(predecessor_sha) != 40:
        raise Refused("NON_EXACT_PREDECESSOR", predecessor_sha)
    admitted_records = [record.admit(window) for record in records]
    order_evidence(admitted_records, evidence_edges)
    current_by_repo = {reconcile_repo([r for r in admitted_records if r.subject.repo == repo]).current_subject for repo in {r.subject.repo for r in admitted_records}}
    requested = set(subjects)
    if not requested.issubset(current_by_repo):
        stale = sorted(subject.coordinate for subject in requested - current_by_repo)
        raise Refused("STALE_OR_UNRECONCILED_SUBJECT", ",".join(stale))
    ordered = dependency_order(subjects, dependencies)
    profile = ObligationProfile()
    admissions = tuple(admit_subject(subject, admitted_records, claims, profile) for subject in ordered)
    steps = build_plan(list(admissions), authority)
    evidence_ids = sorted({evidence_id for admission in admissions for evidence_id in admission.evidence_ids})
    receipt = manufacture_receipt(predecessor_sha, [s.coordinate for s in ordered], evidence_ids, steps)
    replay(receipt)
    return PromotionResult(tuple(s.coordinate for s in ordered), admissions, steps, receipt)
