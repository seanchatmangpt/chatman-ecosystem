from dataclasses import dataclass
from . import DependencySubject, Refusal

@dataclass(frozen=True)
class Candidate:
    subject: DependencySubject
    release_criticality: int
    blockers_removed: int
    evidence: str

    @property
    def score(self): return self.release_criticality * 100 + self.blockers_removed * 10 + (1 if self.evidence == 'exact-head-success' else 0)

def select(candidates: list[Candidate]) -> Candidate:
    viable=[c for c in candidates if c.evidence in {'exact-head-success','exact-head-partial'}]
    if not viable: raise Refusal('REFUSED[NO_EVIDENCE_BACKED_CANDIDATE]')
    return sorted(viable, key=lambda c:(-c.score,c.subject.key))[0]
