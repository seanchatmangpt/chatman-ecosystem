from dataclasses import dataclass
from fractions import Fraction
from .trajectory import Trajectory

@dataclass(frozen=True)
class Efficiency:
    information_per_cost: Fraction
    information_per_sample: Fraction
    latency_per_bit: Fraction | None

    @classmethod
    def from_trajectory(cls, trajectory: Trajectory):
        gain=sum((s.realized_gain for s in trajectory.steps), Fraction())
        cost=sum((s.cost for s in trajectory.steps), Fraction())
        latency=sum((s.latency for s in trajectory.steps), Fraction())
        samples=sum(s.samples for s in trajectory.steps)
        return cls(gain/cost if cost else gain, gain/samples, latency/gain if gain else None)
