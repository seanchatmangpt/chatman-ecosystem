from dataclasses import dataclass
import hashlib,json
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject: str
    generation: int
    standing: str
    calibration_digest: str
    authority: str="SELECT"
    actuation_performed: bool=False
    def __post_init__(self):
        if self.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}: raise Refused("INVALID_RECEIPT_AUTHORITY")
        if self.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    @property
    def body(self): return {"schema":"chatman.develop-federation-convergence-realization-control/1","subject":self.subject,"generation":self.generation,"standing":self.standing,"calibration_digest":self.calibration_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
