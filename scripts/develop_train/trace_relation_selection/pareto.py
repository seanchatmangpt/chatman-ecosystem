from dataclasses import dataclass
from .calibration import CalibrationEvidence
from .wilson import wilson_upper

@dataclass(frozen=True)
class Candidate:
    evidence: CalibrationEvidence

    @property
    def objectives(self):
        e = self.evidence
        return (
            wilson_upper(e.false_equivalence, e.support),
            wilson_upper(e.false_refusal, e.support),
            float(e.evaluation_cost),
        )

def dominates(a: Candidate, b: Candidate) -> bool:
    ao, bo = a.objectives, b.objectives
    return all(x <= y for x, y in zip(ao, bo)) and any(x < y for x, y in zip(ao, bo))

def frontier(evidence):
    candidates = tuple(Candidate(e) for e in evidence)
    return tuple(sorted(
        (c for c in candidates if not any(dominates(o, c) for o in candidates if o != c)),
        key=lambda c: c.evidence.relation.value,
    ))
