from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class InvarianceConfusion:
    true_stable:int
    false_stable:int
    true_unstable:int
    false_unstable:int
    @property
    def support(self): return self.true_stable+self.false_stable+self.true_unstable+self.false_unstable
    @property
    def false_stable_rate(self):
        d=self.true_stable+self.false_stable
        return Fraction(self.false_stable,d) if d else Fraction(0)
    @property
    def false_unstable_rate(self):
        d=self.true_unstable+self.false_unstable
        return Fraction(self.false_unstable,d) if d else Fraction(0)
def confusion(cases):
    ts=fs=tu=fu=0
    for c in cases:
        if c.predicted_invariant and c.observed_success: ts+=1
        elif c.predicted_invariant and not c.observed_success: fs+=1
        elif not c.predicted_invariant and not c.observed_success: tu+=1
        else: fu+=1
    return InvarianceConfusion(ts,fs,tu,fu)
