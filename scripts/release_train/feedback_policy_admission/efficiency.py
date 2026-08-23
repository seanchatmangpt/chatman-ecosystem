from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Efficiency:
    bits_per_cost: Fraction
    bits_per_sample: Fraction
    latency_per_bit: Fraction
    @classmethod
    def from_trajectory(cls,t):
        gain=t.total_realized
        cost=sum((s.cost for s in t.steps),0)
        samples=sum(s.samples for s in t.steps)
        latency=sum((s.latency for s in t.steps),0)
        if gain <= 0: raise Refused("ZERO_REALIZED_INFORMATION")
        if cost <= 0 or samples <= 0: raise Refused("INVALID_RESOURCE_DENOMINATOR")
        return cls(gain/cost, gain/samples, latency/gain)
