from dataclasses import dataclass
from .confusion import confusion
@dataclass(frozen=True)
class Calibration:
    sensor_id:str
    generation:int
    support:int
    false_current_rate:float
    false_stale_rate:float
    ambiguity_rate:float
def calibrate(sensor,trials):
    rows=[t for t in trials if t.sensor==sensor]
    c=confusion(rows)
    return Calibration(sensor.sensor_id,sensor.generation,c.support,c.false_current_rate,c.false_stale_rate,(c.ambiguous/c.support if c.support else 0.0))
