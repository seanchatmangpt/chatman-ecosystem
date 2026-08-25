from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True,order=True)
class Stratum:
    methodology:str; engine:str; region:str; evidence_root:str
    def __post_init__(self):
        if not all((self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("REFUSED[INCOMPLETE_STRATUM]")
