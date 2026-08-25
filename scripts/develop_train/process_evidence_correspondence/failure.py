from .errors import Refused
REQUIRED_FAILURES=frozenset({"NODE_DOWN","PARTITION","LATENCY","LOSS","VERSION_SKEW","CERTIFICATE","AMBIGUOUS_DO"})
def require_failure_worlds(worlds):
    missing=sorted(REQUIRED_FAILURES-set(worlds))
    if missing: raise Refused("INCOMPLETE_FAILURE_WORLDS",",".join(missing))
    return True
def combine_standing(states):
    s=set(states)
    if "BUILD_BROKEN" in s: return "BUILD_BROKEN"
    if s & {"SECURITY_FAILURE","AUTHORITY_FAILURE"}: return "UNKNOWN"
    if "UNKNOWN" in s: return "UNKNOWN"
    if "PARTIAL_ALIVE" in s or "ALIVE" in s: return "PARTIAL_ALIVE"
    return "UNKNOWN"
