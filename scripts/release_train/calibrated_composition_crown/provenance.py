from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Provenance:
    implementation:str; model:str; domain:str
def require_independent(a,b):
    if not all((a.implementation!=b.implementation,a.model!=b.model,a.domain!=b.domain)):
        raise Refused("UNPROVEN_INDEPENDENCE")
    return True
