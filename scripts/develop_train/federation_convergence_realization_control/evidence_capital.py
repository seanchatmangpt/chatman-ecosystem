from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class EvidenceCapital:
    nominal: int
    independent_units: int
    effective: float
    @property
    def admitted(self): return self.effective >= 2.0
def capital(observations):
    obs=tuple(observations)
    units=min(len({o.evidence_root for o in obs}),len({o.engine for o in obs}),len({o.region for o in obs}))
    return EvidenceCapital(len(obs),units,min(float(len(obs)),float(units)))
def require_capital(value):
    if not value.admitted: raise Refused("PSEUDO_CONVERGENCE_CAPITAL")
    return value
