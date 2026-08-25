from dataclasses import dataclass,asdict
import hashlib,json
from .errors import Refused
@dataclass(frozen=True, slots=True)
class Receipt:
    subject:str; generation:int; policy_digest:str; strategy:str; standing:str; actuation_performed:bool=False
    def body(self): return asdict(self)
    def digest(self): return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def replay(receipt,digest):
    if receipt.actuation_performed: raise Refused('REFUSED_RECEIPT_REPORTS_ACTUATION')
    if receipt.digest()!=digest: raise Refused('REFUSED_RECEIPT_TAMPER')
    return 'REPLAY_MATCH'
