from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class DirectionalRisk: false_current:int; false_stale:int; support:int; loss:Fraction
def evaluate(xs,false_current_cost=5,false_stale_cost=1):
    xs=tuple(xs)
    if not xs: raise Refused("EMPTY_DIRECTIONAL_SAMPLE")
    fc=sum(x.predicted_current and not x.realized_current for x in xs); fs=sum((not x.predicted_current) and x.realized_current for x in xs)
    return DirectionalRisk(fc,fs,len(xs),Fraction(fc*false_current_cost+fs*false_stale_cost,len(xs)))
