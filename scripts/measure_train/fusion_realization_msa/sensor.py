from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class SensorIdentity:
    sensor_id: str
    family: str
    runtime: str
    artifact_digest: str
    calibration_digest: str
    def __post_init__(self):
        if not all(x.strip() for x in (self.sensor_id,self.family,self.runtime)): raise Refused("REFUSED[INVALID_SENSOR_IDENTITY]")
        for name,value in (("artifact",self.artifact_digest),("calibration",self.calibration_digest)):
            if len(value)!=64 or any(c not in "0123456789abcdef" for c in value): raise Refused(f"REFUSED[INVALID_{name.upper()}_DIGEST]")
