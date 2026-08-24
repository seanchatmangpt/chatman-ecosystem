from dataclasses import dataclass
import hashlib, json
from .realization import evaluate

@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    false_current_rate: float
    false_stale_rate: float
    realized_loss: float

    @property
    def admitted(self):
        return self.support >= 5 and self.false_current_rate <= 0.2

def calibrate(observations, generation: int) -> Calibration:
    metric = evaluate(observations)
    body = {"generation":generation,"support":metric.support,"false_current":metric.false_current,"false_stale":metric.false_stale,"loss":round(metric.realized_loss,12)}
    digest = hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Calibration(generation,digest,metric.support,metric.false_current/metric.support,metric.false_stale/metric.support,metric.realized_loss)
