from .errors import Refused
REQUIRED=frozenset({"NODE","PARTITION","LATENCY","LOSS","VERSION","CERTIFICATE","AMBIGUOUS_DO"})
def require_failures(worlds):
    if set(worlds)!=REQUIRED: raise Refused("INCOMPLETE_FAILURE_CLOSURE")
    return True
