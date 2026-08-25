from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
from .realization import StepRealization

@dataclass(frozen=True)
class FailureWorld:
    seed: str
    bias: Fraction = Fraction()
    latency_multiplier: Fraction = Fraction(1)

    def apply(self, step: StepRealization):
        bit=int(hashlib.sha256(f"{self.seed}:{step.evidence_id}".encode()).hexdigest(),16)&1
        realized=max(Fraction(), step.realized_gain + (self.bias if bit else -self.bias))
        return replace(step, realized_gain=realized, latency=step.latency*self.latency_multiplier)
