from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True, order=True)
class RobustnessBound:
    lower: Fraction
    upper: Fraction
    gamma: Fraction
    estimator: str
    model_digest: str
    def __post_init__(self):
        if self.lower > self.upper: raise Refused("REFUSED[REVERSED_BOUND]")
        if self.gamma < 1: raise Refused("REFUSED[INVALID_GAMMA]")
        if len(self.model_digest) != 64: raise Refused("REFUSED[INVALID_MODEL_DIGEST]")
        if not self.estimator.strip(): raise Refused("REFUSED[EMPTY_ESTIMATOR]")
    @property
    def width(self): return self.upper-self.lower
