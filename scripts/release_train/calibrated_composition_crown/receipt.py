from dataclasses import dataclass,asdict
import hashlib,json
from .refusal import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str; generation:int; strategy:str; mode:str; standing:str; blockers:tuple; authority:str="SELECT"; actuation_performed:bool=False
    def body(self): return asdict(self)
    def digest(self): return hashlib.sha256(json.dumps(self.body(),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def replay(receipt,digest):
    if receipt.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.digest()!=digest: raise Refused("RECEIPT_DRIFT")
    return "REPLAY_MATCH"
