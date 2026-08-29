from .errors import Refused
def zero_red(o): return o.realized_blockers==0 and o.realized_errors==0 and o.realized_churn==0
def dwell(trajectory):
    n=0
    for o in reversed(trajectory.observations):
        if zero_red(o): n+=1
        else: break
    return n
def require_dwell(trajectory, minimum=2):
    value=dwell(trajectory)
    if value < minimum: raise Refused("INSUFFICIENT_ZERO_RED_DWELL")
    return value
