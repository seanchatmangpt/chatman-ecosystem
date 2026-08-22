from dataclasses import dataclass
from .subject import Subject
class CandidateRefusal(ValueError): pass
@dataclass(frozen=True)
class PromotionCandidate:
    component: str
    current: Subject
    proposed: Subject
    criticality: int
    reversible: bool
    evidence_state: str
    def __post_init__(self):
        if self.current.repo != self.proposed.repo: raise CandidateRefusal("REFUSED[FOREIGN_PROMOTION]")
        if self.current.sha == self.proposed.sha: raise CandidateRefusal("REFUSED[NO_MOVEMENT]")
        if not 1 <= self.criticality <= 5: raise CandidateRefusal("REFUSED[INVALID_CRITICALITY]")
        if not self.reversible: raise CandidateRefusal("REFUSED[IRREVERSIBLE_CANDIDATE]")
