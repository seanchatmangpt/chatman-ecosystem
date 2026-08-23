from dataclasses import dataclass
from fractions import Fraction
import re
from .fractions import unit
from .refusals import Refused

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    false_current: Fraction
    false_stale: Fraction
    ambiguity: Fraction

    def __post_init__(self):
        if self.generation < 0 or self.support < 1 or not _HEX64.fullmatch(self.digest):
            raise Refused("INVALID_CALIBRATION_IDENTITY")
        object.__setattr__(self, "false_current", unit(self.false_current, "false_current"))
        object.__setattr__(self, "false_stale", unit(self.false_stale, "false_stale"))
        object.__setattr__(self, "ambiguity", unit(self.ambiguity, "ambiguity"))

    @property
    def error_mass(self) -> Fraction:
        return self.false_current + self.false_stale + self.ambiguity
