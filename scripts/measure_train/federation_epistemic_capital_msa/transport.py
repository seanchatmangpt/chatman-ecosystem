from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True,order=True)
class Transport:
    transport_id:str; implementation_digest:str; model_digest:str; domain:str; generation:int
    def __post_init__(self):
        if not self.transport_id or not self.domain: raise Refused("REFUSED[INVALID_TRANSPORT_IDENTITY]")
        if len(self.implementation_digest)!=64 or len(self.model_digest)!=64: raise Refused("REFUSED[INVALID_PROVENANCE]")
        if self.generation<0: raise Refused("REFUSED[INVALID_GENERATION]")
