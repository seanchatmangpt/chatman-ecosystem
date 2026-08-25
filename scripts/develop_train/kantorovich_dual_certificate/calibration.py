from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    coverage: Fraction
    max_gap: Fraction
    max_witness_error: Fraction
    def admitted(self, min_support=5, min_coverage=Fraction(4,5), max_gap=Fraction(0), max_witness_error=Fraction(1,10)):
        return self.support >= min_support and self.coverage >= min_coverage and self.max_gap <= max_gap and self.max_witness_error <= max_witness_error

def current(calibrations):
    calibrations = tuple(calibrations)
    if not calibrations:
        raise Refused("NO_CALIBRATION_FRONTIER")
    generation = max(item.generation for item in calibrations)
    latest = [item for item in calibrations if item.generation == generation]
    if len({item.digest for item in latest}) != 1:
        raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return sorted(latest, key=lambda item: item.digest)[0]
