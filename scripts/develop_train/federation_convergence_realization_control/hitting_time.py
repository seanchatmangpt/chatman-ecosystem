from .dwell import zero_red
from .errors import Refused
def hitting_generation(trajectory):
    for o in trajectory.observations:
        if zero_red(o): return o.generation
    raise Refused("NO_ZERO_RED_HIT")
