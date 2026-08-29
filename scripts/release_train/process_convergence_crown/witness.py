from .potential import weighted_debt
from .trajectory import Trajectory

def lyapunov_nonincrease(t: Trajectory) -> bool:
    debts=[weighted_debt(e) for e in t.epochs]
    return all(b <= a for a,b in zip(debts,debts[1:]))

def fixed_point(t: Trajectory, dwell: int = 2) -> bool:
    if dwell < 2 or len(t.epochs) < dwell: return False
    tail=t.epochs[-dwell:]
    first=tail[0].states
    return all(e.states == first for e in tail[1:])
