from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Thresholds:
    min_support:int=5; min_coverage:float=.8; max_width:float=.8; max_sensitivity:float=.5
def admit(calibration,sensitivity, thresholds=Thresholds()):
    if calibration.support<thresholds.min_support: raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
    if calibration.coverage<thresholds.min_coverage: raise Refused("UNCALIBRATED_COMPOSITION")
    if calibration.mean_width>thresholds.max_width: raise Refused("VACUOUS_COMPOSITION")
    if max(sensitivity.endpoint_displacement,sensitivity.width_displacement)>thresholds.max_sensitivity: raise Refused("DEPENDENCE_SENSITIVE_COMPOSITION")
    return True
