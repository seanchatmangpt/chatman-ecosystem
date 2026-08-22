from dataclasses import dataclass
@dataclass(frozen=True)
class RiskVector:
    blast_radius:int
    reversibility:int
    evidence_quality:int
    dependency_relief:int
    def __post_init__(self):
        for v in (self.blast_radius,self.reversibility,self.evidence_quality,self.dependency_relief):
            if not 1 <= v <= 5: raise ValueError("REFUSED[INVALID_RISK_VECTOR]")
    @property
    def score(self):
        return self.dependency_relief + self.reversibility + self.evidence_quality - self.blast_radius
