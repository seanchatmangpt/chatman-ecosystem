from .subject import Refused
REQUIRED={"NODE_DOWN","PARTITION","LATENCY","LOSS","VERSION_SKEW","CERTIFICATE","AMBIGUOUS_DO"}
def require_complete(worlds):
    present=set(worlds); missing=REQUIRED-present
    if missing: raise Refused("REFUSED[INCOMPLETE_FAILURE_WORLD_COVERAGE]")
    return tuple(sorted(present))
