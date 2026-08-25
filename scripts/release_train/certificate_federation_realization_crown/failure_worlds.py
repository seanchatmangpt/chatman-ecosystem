from .refusal import Refused
REQUIRED=frozenset({"node","partition","latency","loss","version","certificate","ambiguous-do"})

def require_failure_worlds(worlds) -> frozenset[str]:
    got=frozenset(worlds); missing=REQUIRED-got
    if missing: raise Refused("INCOMPLETE_FAILURE_WORLD_CLOSURE", ",".join(sorted(missing)))
    return got
