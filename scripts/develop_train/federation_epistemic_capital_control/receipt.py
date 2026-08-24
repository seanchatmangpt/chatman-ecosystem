from dataclasses import dataclass
import hashlib,json
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; standing:str; calibration_digest:str; effective_capital:str; authority:str='SELECT'; actuation_performed:bool=False
    def __post_init__(self):
        if self.authority not in {'OBSERVE','SELECT','CONSTRUCT','VERIFY'}: raise Refused('INVALID_RECEIPT_AUTHORITY')
        if self.actuation_performed: raise Refused('REPORTED_AMBIENT_ACTUATION')
    @property
    def body(self): return {'schema':'chatman.develop-federation-epistemic-capital-control/1','subject':self.subject,'generation':self.generation,'standing':self.standing,'calibration_digest':self.calibration_digest,'effective_capital':self.effective_capital,'authority':self.authority,'actuation_performed':self.actuation_performed}
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def replay(r,d):
    if r.digest!=d: raise Refused('RECEIPT_DIGEST_MISMATCH')
    return 'REPLAY_MATCH'
