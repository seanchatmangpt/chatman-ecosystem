from dataclasses import dataclass
from fractions import Fraction
from .interval import Interval
from .identity import PolicyIdentity
@dataclass(frozen=True)
class PolicyBound:
    policy:PolicyIdentity
    utility:Interval
    breakdown_gamma:Fraction
    cost:Fraction
    latency:Fraction
    calibration_generation:int
    calibration_digest:str
    evidence_ids:tuple
    def __post_init__(self):
        if self.breakdown_gamma<1 or self.cost<0 or self.latency<0: raise ValueError('invalid policy bound')
