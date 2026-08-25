from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from .perturbation import Perturbation, apply_pair
from .population import Population

class StressKind(str, Enum):
    SUPPORT_EROSION="support_erosion"
    TARGET_SHIFT="target_shift"
    WEIGHT_CONCENTRATION="weight_concentration"
    ESTIMATOR_DIVERGENCE="estimator_divergence"
    CALIBRATION_DRIFT="calibration_drift"
    ENGINE_DIVERGENCE="engine_divergence"
    REGION_FAILURE="region_failure"

@dataclass(frozen=True)
class StressWorld:
    kind: StressKind
    cell: str
    magnitude: Fraction

    def populations(self, source: Population, target: Population) -> tuple[Population,Population]:
        if self.kind == StressKind.SUPPORT_EROSION:
            return apply_pair(source,target,Perturbation(self.cell,-abs(self.magnitude),Fraction(0)))
        if self.kind == StressKind.TARGET_SHIFT:
            return apply_pair(source,target,Perturbation(self.cell,Fraction(0),abs(self.magnitude)))
        return source,target
