from dataclasses import dataclass
from .identity import Subject
from .methodology import MethodologyCoverage
from .obligations import ClosureCensus, Obligation
from .standing import Standing, compute
from .rail_evidence import RailEvidence
from .refusal import require

@dataclass(frozen=True)
class Qualification:
    subject: Subject
    coverage: MethodologyCoverage
    census: ClosureCensus
    rails: tuple[RailEvidence, ...]
    blockers: tuple[str, ...]
    standing: Standing
    reasons: tuple[str, ...]

def qualify(subject, coverage, satisfied, failed=frozenset(), rails=(), blockers=(), crown_mode=False):
    require(all(r.subject == subject for r in rails), "FOREIGN_QUALIFICATION_SUBJECT")
    sat=set(satisfied)
    if coverage.complete: sat.add(Obligation.METHODOLOGY_COVERAGE)
    census=ClosureCensus(frozenset(sat), frozenset(failed))
    standing=compute(census, tuple(r.outcome for r in rails), blockers, crown_mode=crown_mode)
    reasons=tuple(census.failures)+tuple(census.missing)+tuple(sorted(blockers))
    return Qualification(subject,coverage,census,tuple(rails),tuple(blockers),standing,reasons)
