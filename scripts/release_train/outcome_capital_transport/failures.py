from .errors import Refused
REQUIRED=frozenset({"NODE","PARTITION","LATENCY","LOSS","VERSION","CERTIFICATE","AMBIGUOUS_DO"})
def require_failure_worlds(worlds):
    missing=REQUIRED-set(worlds)
    if missing: raise Refused("INCOMPLETE_FAILURE_TOPOLOGY", ",".join(sorted(missing)))
    return True
