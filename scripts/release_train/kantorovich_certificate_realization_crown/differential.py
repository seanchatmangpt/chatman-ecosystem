from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Differential:
    max_gap: Fraction
    mean_gap: Fraction
def oracle_differential(observations):
    gaps=[abs(o.oracle_cost-o.predicted_bound) for o in observations]
    return Differential(max(gaps), sum(gaps, Fraction())/len(gaps))
