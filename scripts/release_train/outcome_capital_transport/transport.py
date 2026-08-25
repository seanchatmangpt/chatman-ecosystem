from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .support import require_positivity
from .shift import total_variation
from .weights import importance_weights, effective_sample_size

@dataclass(frozen=True)
class TransportModel:
    generation: int
    digest: str
    max_shift: Fraction = Fraction(2,5)
    min_ess: Fraction = Fraction(2)

def admit_transport(source,target,model,sample_cells):
    require_positivity(source,target)
    tv=total_variation(source,target)
    if tv>model.max_shift: raise Refused("TRANSPORT_SHIFT_EXCEEDED", str(tv))
    w=importance_weights(source,target)
    ess=effective_sample_size([w[c] for c in sample_cells])
    if ess<model.min_ess: raise Refused("TRANSPORT_ESS_TOO_LOW", str(ess))
    return {"tv":tv,"ess":ess,"weights":w}
