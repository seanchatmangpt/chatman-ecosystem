from dataclasses import dataclass
from .subject import Subject, Refused
@dataclass(frozen=True, order=True)
class Sensor:
    subject: Subject
    sensor_id: str
    family: str
    domain: str
    generation: int
    calibration_digest: str
    def __post_init__(self):
        if not self.sensor_id.strip() or not self.family.strip() or not self.domain.strip():
            raise Refused("REFUSED[INVALID_SENSOR_IDENTITY]")
        if self.generation < 0:
            raise Refused("REFUSED[INVALID_SENSOR_GENERATION]")
        if len(self.calibration_digest) != 64 or any(c not in "0123456789abcdef" for c in self.calibration_digest):
            raise Refused("REFUSED[INVALID_CALIBRATION_DIGEST]")
