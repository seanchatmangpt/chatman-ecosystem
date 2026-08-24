from .refusal import Refused
REQUIRED_FAILURES=frozenset({"node","partition","latency","loss","version","certificate","ambiguous_do"})
def require_failures(worlds):
    missing=REQUIRED_FAILURES-set(worlds)
    if missing: raise Refused("FAILURE_WORLD_GAP",",".join(sorted(missing)))
    return True
