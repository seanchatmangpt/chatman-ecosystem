from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Contingency2x2:
    n00:int
    n01:int
    n10:int
    n11:int

    @property
    def n(self): return self.n00+self.n01+self.n10+self.n11
    @property
    def p_left(self):
        return Fraction(self.n10+self.n11,self.n) if self.n else Fraction(0)
    @property
    def p_right(self):
        return Fraction(self.n01+self.n11,self.n) if self.n else Fraction(0)
    @property
    def p_joint(self):
        return Fraction(self.n11,self.n) if self.n else Fraction(0)
    @property
    def covariance(self):
        return self.p_joint-self.p_left*self.p_right

def contingency(rows):
    counts={(False,False):0,(False,True):0,(True,False):0,(True,True):0}
    for row in rows:
        counts[(row.left,row.right)] += 1
    return Contingency2x2(counts[(False,False)],counts[(False,True)],counts[(True,False)],counts[(True,True)])
