from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .rational import nonnegative
@dataclass(frozen=True)
class StepRealization:
    step:int; predicted_bits:Fraction; realized_bits:Fraction; cost:Fraction; latency:Fraction
    def __post_init__(self):
        if self.step<0: raise Refused("INVALID_STEP")
        for n in ("predicted_bits","realized_bits","cost","latency"): object.__setattr__(self,n,nonnegative(getattr(self,n)))
    @property
    def information_debt(self): return max(Fraction(0),self.predicted_bits-self.realized_bits)
