from enum import Enum
from .provenance import require_independent
from .refusal import Refused
class Mode(str,Enum):
    CONSERVATIVE="CONSERVATIVE"; INDEPENDENT="INDEPENDENT"
def compose(a, b, mode, prov_a=None, prov_b=None):
    mode=Mode(mode)
    if mode is Mode.CONSERVATIVE: return a.frechet_and(b)
    if prov_a is None or prov_b is None: raise Refused("UNPROVEN_INDEPENDENCE")
    require_independent(prov_a,prov_b)
    return a.independent_and(b)
