from dataclasses import dataclass
from fractions import Fraction
from .fractions import positive
from .refusals import Refused

@dataclass(frozen=True)
class AcquisitionCandidate:
    candidate_id: str
    sensor_id: str
    information_gain: Fraction
    independence_gain: Fraction
    cost: Fraction
    latency: Fraction

    def __post_init__(self):
        if not self.candidate_id or not self.sensor_id: raise Refused("INVALID_ACQUISITION_IDENTITY")
        if self.information_gain < 0 or self.independence_gain < 0: raise Refused("NEGATIVE_ACQUISITION_GAIN")
        object.__setattr__(self,"cost",positive(self.cost,"cost")); object.__setattr__(self,"latency",positive(self.latency,"latency"))

@dataclass(frozen=True)
class Budget:
    max_cost: Fraction
    max_latency: Fraction
    def admits(self,c:AcquisitionCandidate)->bool:
        return c.cost<=self.max_cost and c.latency<=self.max_latency

def select(candidates:list[AcquisitionCandidate], budget:Budget, strategy:str)->AcquisitionCandidate:
    allowed=[c for c in candidates if budget.admits(c)]
    if not allowed: raise Refused("NO_ADMITTED_ACQUISITION")
    keys={
      "MAX_INFORMATION":lambda c:(c.information_gain,-c.cost,-c.latency,c.candidate_id),
      "MAX_INDEPENDENCE":lambda c:(c.independence_gain,c.information_gain,-c.cost,c.candidate_id),
      "MIN_COST":lambda c:(-c.cost,c.information_gain,c.independence_gain,c.candidate_id),
      "MINIMAX_LATENCY":lambda c:(-c.latency,c.information_gain,c.independence_gain,c.candidate_id),
    }
    if strategy not in keys: raise Refused("UNKNOWN_ACQUISITION_STRATEGY")
    return max(allowed,key=keys[strategy])
