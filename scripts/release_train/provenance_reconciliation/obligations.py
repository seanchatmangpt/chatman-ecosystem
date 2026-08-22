from __future__ import annotations

from dataclasses import dataclass

from .claims import EvidenceClaim
from .model import ExactSubject, Refused

MANDATORY = ("focused", "integration", "e2e", "replay", "security", "repository")


@dataclass(frozen=True)
class ObligationProfile:
    required_scopes: tuple[str, ...] = MANDATORY

    def require(self, subject: ExactSubject, claims: list[EvidenceClaim]) -> dict[str, EvidenceClaim]:
        scoped: dict[str, EvidenceClaim] = {}
        for claim in claims:
            claim.admit()
            if claim.subject != subject:
                continue
            if claim.scope in scoped and scoped[claim.scope] != claim:
                raise Refused("DUPLICATE_SCOPE_CLAIM", claim.scope)
            scoped[claim.scope] = claim
        missing = sorted(set(self.required_scopes) - set(scoped))
        if missing:
            raise Refused("INCOMPLETE_RELEASE_OBLIGATIONS", ",".join(missing))
        return scoped
