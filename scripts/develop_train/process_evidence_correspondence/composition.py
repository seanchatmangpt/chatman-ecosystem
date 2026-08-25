from .errors import Refused
from .provenance import require_independent
def compose(a,b,mode):
    if mode=="CONSERVATIVE": return a.interval.conservative_and(b.interval)
    if mode=="INDEPENDENT":
        require_independent(a.provenance,b.provenance)
        return a.interval.independent_and(b.interval)
    raise Refused("INVALID_COMPOSITION_MODE")
