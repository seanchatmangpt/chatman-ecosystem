from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class Validator:
    validator_id:str; oracle_digest:str; implementation_digest:str; model_digest:str; domain:str; evidence_id:str
    def __post_init__(self):
        if not self.validator_id or not self.domain: raise Refused("REFUSED[INVALID_VALIDATOR]")
        for d in (self.oracle_digest,self.implementation_digest,self.model_digest):
            if len(d)!=64: raise Refused("REFUSED[INVALID_VALIDATOR_DIGEST]")
def provenance_distinct(a,b):
    return (a.validator_id!=b.validator_id and a.oracle_digest!=b.oracle_digest and
            a.implementation_digest!=b.implementation_digest and a.model_digest!=b.model_digest and a.domain!=b.domain)
