from enum import Enum
from .errors import Refused
class FailureWorld(str,Enum):
    NODE_DOWN="NODE_DOWN"; PARTITION="PARTITION"; LATENCY="LATENCY"; LOSS="LOSS"; VERSION_SKEW="VERSION_SKEW"; CERTIFICATE="CERTIFICATE"; AMBIGUOUS_DO="AMBIGUOUS_DO"
REQUIRED=frozenset(FailureWorld)
def require_failure_worlds(values):
    missing=REQUIRED-set(values)
    if missing: raise Refused("INCOMPLETE_FAILURE_WORLD", ",".join(sorted(x.value for x in missing)))
    return True
