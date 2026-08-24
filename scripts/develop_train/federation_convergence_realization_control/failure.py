from enum import Enum
from .errors import Refused
class FailureWorld(str,Enum):
    NODE_DOWN="NODE_DOWN"; PARTITION="PARTITION"; LATENCY="LATENCY"; LOSS="LOSS"; VERSION_SKEW="VERSION_SKEW"; CERTIFICATE="CERTIFICATE"; AMBIGUOUS_DO="AMBIGUOUS_DO"
def require_complete(worlds):
    seen={FailureWorld(w) for w in worlds}; missing=set(FailureWorld)-seen
    if missing: raise Refused("INCOMPLETE_FAILURE_TOPOLOGY")
    return frozenset(seen)
