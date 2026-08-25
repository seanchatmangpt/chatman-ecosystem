from enum import Enum
from .trajectory import Trajectory
from .potential import weighted_debt
from .oscillation import oscillating_keys
from .hazard import hazards
from .witness import lyapunov_nonincrease, fixed_point

class Strategy(str,Enum):
    POTENTIAL="POTENTIAL"; HAZARD="HAZARD"; LYAPUNOV="LYAPUNOV"; FIXED_POINT="FIXED_POINT"; MINIMAX="MINIMAX"

def score(t: Trajectory, strategy: Strategy):
    if strategy is Strategy.POTENTIAL:return -weighted_debt(t.current)
    if strategy is Strategy.HAZARD:return hazards(t).balance
    if strategy is Strategy.LYAPUNOV:return int(lyapunov_nonincrease(t))
    if strategy is Strategy.FIXED_POINT:return int(fixed_point(t))
    return (-len(oscillating_keys(t)), -int(max(t.current.states.values(), default=0)))
