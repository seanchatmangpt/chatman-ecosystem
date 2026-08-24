from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Consequence:
    mae: Fraction
    bias: Fraction
    false_safe_rate: Fraction
def evaluate(observations):
    errors=[o.predicted_bound-o.realized_consequence for o in observations]
    return Consequence(sum(map(abs,errors),Fraction())/len(errors), sum(errors,Fraction())/len(errors), Fraction(sum(e < 0 for e in errors),len(errors)))
