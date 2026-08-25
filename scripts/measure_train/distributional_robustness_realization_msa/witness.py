from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class WitnessCalibration:
    support:int; mae:Fraction; underestimates:int
def calibrate_witness(observations,require_observed=True):
    rows=tuple(observations)
    if require_observed and any(r.witness_loss is None for r in rows): raise Refused("REFUSED[UNOBSERVED_WORST_WITNESS]")
    known=[r for r in rows if r.witness_loss is not None]
    if not known: return WitnessCalibration(0,Fraction(0),0)
    gaps=[r.predicted_worst_loss-r.witness_loss for r in known]
    return WitnessCalibration(len(known),sum((abs(g) for g in gaps),Fraction(0))/len(known),sum(1 for g in gaps if g<0))
