from dataclasses import dataclass
from .probability import nonnegative

@dataclass(frozen=True)
class CusumState:
    positive:object=0
    negative:object=0

def advance(state,residual,slack):
    r=nonnegative(abs(residual)); k=nonnegative(slack)
    signed=residual
    return CusumState(max(0,state.positive+signed-k), max(0,state.negative-signed-k))
def drifted(state,threshold): return state.positive>=nonnegative(threshold) or state.negative>=nonnegative(threshold)
