from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from .refusal import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str
    generation:int
    strategy:str
    selection:tuple[str,...]
    standing:str
    actuation_performed:bool=False
    def __post_init__(self):
        if self.actuation_performed: raise Refused('REPORTED_ACTUATION')
    def body(self): return asdict(self)
    def digest(self): return sha256(json.dumps(self.body(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
def replay(receipt:Receipt,digest:str)->bool:
    if receipt.actuation_performed: raise Refused('REPORTED_ACTUATION')
    return receipt.digest()==digest
