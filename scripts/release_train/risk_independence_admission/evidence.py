from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class BetaEvidence:
    independent: int
    dependent: int
    def __post_init__(self):
        if self.independent < 0 or self.dependent < 0: raise Refused('NEGATIVE_EVIDENCE_COUNT')
        if self.independent + self.dependent == 0: raise Refused('EMPTY_DECISION_EVIDENCE')
    @property
    def support(self): return self.independent + self.dependent
    @property
    def p_independent(self): return Fraction(self.independent + 1, self.support + 2)
