from dataclasses import dataclass, asdict
import hashlib,json
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str
    generation:int
    standing:str
    obligation_digest:str
    parent:str|None=None
    actuation_performed:bool=False
    def body(self):
        if self.actuation_performed: raise Refused("REFUSED[AMBIENT_ACTUATION_REPORTED]")
        return asdict(self)
    def digest(self):
        raw=json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()
