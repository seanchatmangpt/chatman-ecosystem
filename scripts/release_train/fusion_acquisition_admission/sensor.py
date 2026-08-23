from dataclasses import dataclass
import re
from .errors import Refused
from .rational import unit
from .subject import Subject

_HEX64 = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, order=True)
class SensorIdentity:
    subject: Subject
    sensor_id: str
    family: str
    domain: str
    generation: int
    calibration_digest: str
    def __post_init__(self):
        if not self.sensor_id or not self.family or not self.domain:
            raise Refused("MALFORMED_SENSOR_IDENTITY")
        if self.generation < 0:
            raise Refused("INVALID_CALIBRATION_GENERATION")
        if not _HEX64.fullmatch(self.calibration_digest):
            raise Refused("INVALID_CALIBRATION_DIGEST")

@dataclass(frozen=True)
class Calibration:
    sensor: SensorIdentity
    support: int
    false_current_rate: object
    false_stale_rate: object
    ambiguity_rate: object
    def __post_init__(self):
        if self.support < 1:
            raise Refused("CALIBRATION_WITHOUT_SUPPORT")
        object.__setattr__(self, "false_current_rate", unit(self.false_current_rate))
        object.__setattr__(self, "false_stale_rate", unit(self.false_stale_rate))
        object.__setattr__(self, "ambiguity_rate", unit(self.ambiguity_rate))
    @property
    def error_mass(self):
        return (self.false_current_rate + self.false_stale_rate + self.ambiguity_rate) / 3
