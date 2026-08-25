from enum import Enum
from .obligation import State

class Standing(str,Enum): BUILD_BROKEN="BUILD_BROKEN"; BLOCKED="BLOCKED"; UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"
def compute(states, blockers=(), oscillations=()):
    values=set(states.values())
    if State.BUILD_BROKEN in values:return Standing.BUILD_BROKEN
    if blockers or State.BLOCKED in values:return Standing.BLOCKED
    if oscillations or any(s in values for s in (State.UNKNOWN,State.UNSUPPORTED,State.REFUSED)):return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
