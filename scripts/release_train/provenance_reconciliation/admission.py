from __future__ import annotations

from dataclasses import dataclass

from .claims import EvidenceClaim, repository_standing
from .model import ExactSubject, Refused
from .obligations import ObligationProfile
from .provenance import EvidenceRecord


@dataclass(frozen=True)
class SubjectAdmission:
    subject: ExactSubject
    standing: str
    evidence_ids: tuple[str, ...]


def admit_subject(subject: ExactSubject, records: list[EvidenceRecord], claims: list[EvidenceClaim], profile: ObligationProfile) -> SubjectAdmission:
    record_ids = {record.evidence_id for record in records if record.subject == subject}
    if not record_ids:
        raise Refused("NO_PROVENANCE_FOR_SUBJECT", subject.coordinate)
    scoped = profile.require(subject, claims)
    for claim in scoped.values():
        missing = set(claim.evidence_ids) - record_ids
        if missing:
            raise Refused("CLAIM_REFERENCES_FOREIGN_EVIDENCE", ",".join(sorted(missing)))
    standing = repository_standing(claims, subject)
    if standing == "ALIVE" and any(claim.standing != "ALIVE" for scope, claim in scoped.items() if scope != "repository"):
        raise Refused("REPOSITORY_ALIVE_LAUNDERS_FAILED_SCOPE", subject.coordinate)
    return SubjectAdmission(subject, standing, tuple(sorted(record_ids)))
