from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from .calibration import GainCalibration
from .drift import PageHinkley
from .efficiency import Efficiency

class Health(StrEnum):
    HEALTHY="HEALTHY"
    UNDER_SUPPORTED="UNDER_SUPPORTED"
    BIASED="BIASED"
    DRIFTED="DRIFTED"
    RESOURCE_INEFFICIENT="RESOURCE_INEFFICIENT"

@dataclass(frozen=True)
class PolicyHealth:
    state: Health
    reason: str

def classify(calibration: GainCalibration, drift: PageHinkley, efficiency: Efficiency):
    if calibration.support < 3:
        return PolicyHealth(Health.UNDER_SUPPORTED, "support")
    if drift.drifted():
        return PolicyHealth(Health.DRIFTED, "page_hinkley")
    if abs(calibration.bias) > Fraction(1,5):
        return PolicyHealth(Health.BIASED, "forecast_bias")
    if efficiency.information_per_cost < Fraction(1,10):
        return PolicyHealth(Health.RESOURCE_INEFFICIENT, "information_per_cost")
    return PolicyHealth(Health.HEALTHY, "current")
