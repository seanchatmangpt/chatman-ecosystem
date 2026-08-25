from enum import Enum
from .trajectory import Trajectory
from .potential import potential_vector
from .oscillation import oscillating_keys
from .hazard import hazards
from .witness import lyapunov_witness

class Strategy(str, Enum):
    POTENTIAL="POTENTIAL"
    HAZARD="HAZARD"
    LYAPUNOV="LYAPUNOV"
    MINIMAX="MINIMAX"


def classify(traj: Trajectory, strategy: Strategy) -> str:
    first,last=traj.epochs[0],traj.epochs[-1]
    if oscillating_keys(traj): return "OSCILLATING"
    h=hazards(traj)
    if strategy is Strategy.HAZARD:
        if h.regression > h.discharge: return "REGRESSING"
        if h.discharge > h.regression: return "CONVERGING"
        return "STALLED"
    if strategy is Strategy.LYAPUNOV:
        w=lyapunov_witness(traj)
        return "CONVERGING" if w.nonincreasing and w.strictly_decreased else "STALLED"
    if strategy is Strategy.MINIMAX:
        a=potential_vector(first)[1]; b=potential_vector(last)[1]
        return "CONVERGING" if b<a else ("REGRESSING" if b>a else "STALLED")
    a=potential_vector(first)[0]; b=potential_vector(last)[0]
    return "CONVERGING" if b<a else ("REGRESSING" if b>a else "STALLED")
