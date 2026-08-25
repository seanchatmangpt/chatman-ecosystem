from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Confusion:
    true_accept:int
    false_accept:int
    true_refuse:int
    false_refuse:int

    @property
    def support(self):
        return self.true_accept+self.false_accept+self.true_refuse+self.false_refuse

    @property
    def precision(self):
        d=self.true_accept+self.false_accept
        return Fraction(self.true_accept,d) if d else Fraction(0)

    @property
    def recall(self):
        d=self.true_accept+self.false_refuse
        return Fraction(self.true_accept,d) if d else Fraction(0)

    @property
    def false_positive_rate(self):
        d=self.false_accept+self.true_refuse
        return Fraction(self.false_accept,d) if d else Fraction(0)

def confusion(cases, relation):
    rows=[c for c in cases if c.relation==relation]
    return Confusion(
        sum(c.expected and c.observed for c in rows),
        sum((not c.expected) and c.observed for c in rows),
        sum((not c.expected) and (not c.observed) for c in rows),
        sum(c.expected and (not c.observed) for c in rows),
    )
