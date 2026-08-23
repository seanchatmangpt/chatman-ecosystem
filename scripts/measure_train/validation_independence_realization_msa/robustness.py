from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Robustness:
    max_overlap:Fraction; max_inflation:Fraction; leave_one_out_flip_rate:Fraction
def summarize(overlaps,inflations,flips):
    overlaps=tuple(overlaps); inflations=tuple(inflations); flips=tuple(flips)
    return Robustness(max(overlaps,default=Fraction(0)),max(inflations,default=Fraction(0)),Fraction(sum(bool(x) for x in flips),len(flips)) if flips else Fraction(0))
