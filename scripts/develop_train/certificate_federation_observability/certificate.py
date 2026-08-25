from dataclasses import dataclass
import re
from .errors import Refused
HX=re.compile(r"^[0-9a-f]{64}$")
@dataclass(frozen=True)
class Certificate:
    generation:int; digest:str; primal_digest:str; dual_digest:str; realization_digest:str
    def __post_init__(self):
        if self.generation<0 or not all(HX.fullmatch(x) for x in (self.digest,self.primal_digest,self.dual_digest,self.realization_digest)): raise Refused("INVALID_CERTIFICATE_IDENTITY")
