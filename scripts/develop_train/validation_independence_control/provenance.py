from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Provenance:
    implementation: str
    model: str
    domain: str
    def __post_init__(self):
        if not all((self.implementation,self.model,self.domain)): raise Refused("INVALID_PROVENANCE")
def require_distinct(a: Provenance,b: Provenance):
    if a.implementation==b.implementation or a.model==b.model or a.domain==b.domain:
        raise Refused("UNPROVEN_PROVENANCE_INDEPENDENCE")
    return True
