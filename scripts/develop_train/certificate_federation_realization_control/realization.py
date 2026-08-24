from dataclasses import dataclass
from .observation import TransportState
from .errors import Refused

@dataclass(frozen=True)
class DirectionalError:
    support: int
    false_current: int
    false_stale: int
    accuracy: float
    realized_loss: float

def evaluate(observations, false_current_cost=5.0, false_stale_cost=1.0) -> DirectionalError:
    resolved = [o for o in observations if o.state == TransportState.RESOLVED and o.realized_current is not None]
    if not resolved:
        raise Refused("NO_REALIZED_CURRENTNESS_LABELS")
    fc = sum(o.predicted_current and not o.realized_current for o in resolved)
    fs = sum((not o.predicted_current) and o.realized_current for o in resolved)
    correct = len(resolved)-fc-fs
    loss = (fc*false_current_cost + fs*false_stale_cost)/len(resolved)
    return DirectionalError(len(resolved), fc, fs, correct/len(resolved), loss)
