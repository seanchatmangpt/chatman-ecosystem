from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Provenance:
    implementation:str; model:str; domain:str
def require_independent(a:Provenance,b:Provenance):
    if not (a.implementation!=b.implementation and a.model!=b.model and a.domain!=b.domain):
        raise Refused("UNPROVEN_INDEPENDENCE")
    return True
