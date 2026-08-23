from dataclasses import dataclass
from fractions import Fraction
from .refusal import refuse

@dataclass(frozen=True)
class Calibration:
    estimator_id: str
    generation: int
    digest: str
    support: int
    mae: Fraction
    implementation_digest: str
    model_digest: str|None=None
    def __post_init__(self):
        if self.generation<0 or self.support<0 or self.mae<0 or self.mae>1: refuse("INVALID_CALIBRATION")
        for d in (self.digest,self.implementation_digest):
            if len(d)!=64 or any(c not in '0123456789abcdef' for c in d): refuse("INVALID_CALIBRATION")
        if self.model_digest is not None and (len(self.model_digest)!=64 or any(c not in '0123456789abcdef' for c in self.model_digest)): refuse("INVALID_CALIBRATION")

def require_quality(c, *, min_support=3, max_mae=Fraction(1,4)):
    if c.support<min_support: refuse("UNDER_CALIBRATED_ESTIMATOR")
    if c.mae>max_mae: refuse("UNRELIABLE_ESTIMATOR")
    return c
