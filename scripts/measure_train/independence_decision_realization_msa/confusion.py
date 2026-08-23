from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class DecisionConfusion:
    support:int; correct:int; false_independent:int; false_dependent:int; deferred:int
    @property
    def accuracy(self): return Fraction(self.correct,self.support) if self.support else Fraction(0)
    @property
    def false_independent_rate(self): return Fraction(self.false_independent,self.support) if self.support else Fraction(0)
    @property
    def false_dependent_rate(self): return Fraction(self.false_dependent,self.support) if self.support else Fraction(0)
    @property
    def defer_rate(self): return Fraction(self.deferred,self.support) if self.support else Fraction(0)
def confusion(rows):
    rows=tuple(rows); correct=fi=fd=defer=0
    for row in rows:
        if row.decision=="DEFER": defer+=1
        elif row.decision==row.truth: correct+=1
        elif row.decision=="INDEPENDENT": fi+=1
        else: fd+=1
    return DecisionConfusion(len(rows),correct,fi,fd,defer)
