from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
STRESS_KINDS={"SUPPORT_EROSION","TARGET_SHIFT","WEIGHT_CONCENTRATION","ESS_COLLAPSE","ESTIMATOR_DISAGREEMENT","CALIBRATION_DRIFT","LOCAL_STRATUM_FAILURE"}
@dataclass(frozen=True, order=True)
class StressIdentity:
    stress_id: str
    kind: str
    magnitude: Fraction
    generation: int
    def __post_init__(self):
        if not self.stress_id: raise Refused("REFUSED[EMPTY_STRESS_ID]")
        if self.kind not in STRESS_KINDS: raise Refused("REFUSED[UNKNOWN_STRESS_KIND]")
        if not (Fraction(0)<=self.magnitude<=Fraction(1)): raise Refused("REFUSED[INVALID_STRESS_MAGNITUDE]")
        if self.generation<0: raise Refused("REFUSED[INVALID_STRESS_GENERATION]")
