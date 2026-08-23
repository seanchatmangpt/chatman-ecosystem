from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class FusionTopology:
    state:str
    score:Fraction
    independent_count:int

def classify(score:Fraction, independent_count:int, min_independent:int=2)->FusionTopology:
    if independent_count<min_independent: return FusionTopology("UNDER_SUPPORTED",score,independent_count)
    if score>Fraction(1,4): return FusionTopology("CURRENT",score,independent_count)
    if score<Fraction(-1,4): return FusionTopology("STALE",score,independent_count)
    return FusionTopology("AMBIGUOUS",score,independent_count)
