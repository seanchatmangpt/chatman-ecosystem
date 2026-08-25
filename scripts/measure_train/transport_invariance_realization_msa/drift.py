from dataclasses import dataclass
from fractions import Fraction
@dataclass
class Cusum:
    threshold:Fraction
    slack:Fraction=Fraction(0)
    value:Fraction=Fraction(0)
    def update(self,observed,target):
        self.value=max(Fraction(0),self.value+observed-target-self.slack); return self.value
    @property
    def changed(self): return self.value>=self.threshold
