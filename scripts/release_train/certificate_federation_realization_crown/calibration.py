from dataclasses import dataclass
from hashlib import sha256
import json
from .realization import DirectionalError
from .refusal import Refused

@dataclass(frozen=True)
class Calibration:
    generation: int
    support: int
    false_current_rate: float
    false_stale_rate: float
    loss: float
    digest: str

def calibrate(generation: int, err: DirectionalError) -> Calibration:
    if err.support < 2:
        raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
    body={"generation":generation,"support":err.support,"false_current_rate":err.false_current/err.support,
          "false_stale_rate":err.false_stale/err.support,"loss":err.loss}
    digest=sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Calibration(**body,digest=digest)

def current(models: list[Calibration]) -> Calibration:
    if not models: raise Refused("NO_CALIBRATION")
    g=max(m.generation for m in models)
    latest=[m for m in models if m.generation==g]
    if len({m.digest for m in latest}) != 1:
        raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return latest[0]
