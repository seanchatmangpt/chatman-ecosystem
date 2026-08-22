from __future__ import annotations

from dataclasses import dataclass

from .model import ExactSubject, Refused

STANDINGS = frozenset({"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"})
SCOPES = frozenset({"focused", "unit", "integration", "e2e", "replay", "security", "repository"})


@dataclass(frozen=True)
class EvidenceClaim:
    claim_id: str
    subject: ExactSubject
    scope: str
    standing: str
    evidence_ids: tuple[str, ...]

    def admit(self) -> "EvidenceClaim":
        if not self.claim_id.strip():
            raise Refused("MISSING_CLAIM_ID")
        if self.scope not in SCOPES:
            raise Refused("UNSUPPORTED_CLAIM_SCOPE", self.scope)
        if self.standing not in STANDINGS:
            raise Refused("INVALID_STANDING", self.standing)
        if not self.evidence_ids:
            raise Refused("EVIDENCE_FREE_CLAIM", self.claim_id)
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise Refused("DUPLICATE_CLAIM_EVIDENCE", self.claim_id)
        return self


def repository_standing(claims: list[EvidenceClaim], subject: ExactSubject) -> str:
    admitted = [claim.admit() for claim in claims if claim.subject == subject]
    repository = [claim for claim in admitted if claim.scope == "repository"]
    if repository:
        values = {claim.standing for claim in repository}
        if len(values) != 1:
            raise Refused("CONTRADICTORY_REPOSITORY_STANDING", subject.coordinate)
        return next(iter(values))
    if any(claim.standing in {"BLOCKED", "BUILD_BROKEN"} for claim in admitted):
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
