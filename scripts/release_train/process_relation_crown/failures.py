from .refusal import Refused
REQUIRED=frozenset({"node","partition","latency","loss","version","certificate","ambiguous_do"})
def require_complete(values):
    missing=REQUIRED-set(values)
    if missing: raise Refused("FAILURE_WORLD_GAP:"+",".join(sorted(missing)))
    return True
