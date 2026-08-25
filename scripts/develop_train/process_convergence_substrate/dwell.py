from .trajectory import Trajectory
from .obligation import State


def dwell(traj: Trajectory, target: State = State.PASS) -> int:
    count=0
    for e in reversed(traj.epochs):
        if all(o.state == target for o in e.obligations):
            count += 1
        else:
            break
    return count
