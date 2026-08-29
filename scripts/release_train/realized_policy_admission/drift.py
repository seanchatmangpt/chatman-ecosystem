from dataclasses import dataclass

@dataclass(frozen=True)
class DriftState:
    cumulative: float=0.0
    minimum: float=0.0
    drifted: bool=False

def page_hinkley(state: DriftState, residual: float, delta: float, threshold: float):
    if delta < 0 or threshold <= 0:
        raise ValueError("REFUSED[INVALID_DRIFT_PARAMETERS]")
    cumulative=state.cumulative+residual-delta
    minimum=min(state.minimum,cumulative)
    return DriftState(cumulative, minimum, state.drifted or (cumulative-minimum)>threshold)
