from dataclasses import dataclass
from .refusal import Refused
from .transport import Observation, TransportState

@dataclass(frozen=True)
class DirectionalError:
    support: int
    false_current: int
    false_stale: int
    loss: float

def evaluate(observations: tuple[Observation, ...], false_current_cost: float=5.0, false_stale_cost: float=1.0) -> DirectionalError:
    if false_current_cost <= false_stale_cost or false_stale_cost < 0:
        raise Refused("INVALID_ASYMMETRIC_LOSS")
    resolved=[o for o in observations if o.state == TransportState.RESOLVED and o.realized_current is not None]
    if not resolved:
        raise Refused("NO_REALIZED_OBSERVATIONS")
    fc=sum(o.predicted_current and not o.realized_current for o in resolved)
    fs=sum((not o.predicted_current) and o.realized_current for o in resolved)
    return DirectionalError(len(resolved), fc, fs, (fc*false_current_cost+fs*false_stale_cost)/len(resolved))
