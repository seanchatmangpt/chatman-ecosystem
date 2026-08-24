from dataclasses import dataclass,asdict
import hashlib,json
from .refusal import Refused
def _digest(body): return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":" )).encode()).hexdigest()
@dataclass(frozen=True)
class Receipt:
    schema:str; subject:str; standing:str; evidence_digest:str; authority:str="SELECT"; actuation_performed:bool=False; digest:str=""
    @classmethod
    def issue(cls,subject,standing,evidence_digest):
        body={"schema":"chatman.distributional-robustness-crown/1","subject":subject,"standing":standing,"evidence_digest":evidence_digest,"authority":"SELECT","actuation_performed":False}
        return cls(**body,digest=_digest(body))
def replay(receipt):
    body=asdict(receipt); got=body.pop("digest")
    if body["authority"]!="SELECT" or body["actuation_performed"]: raise Refused("RECEIPT_AUTHORITY_DRIFT")
    if got!=_digest(body): raise Refused("RECEIPT_TAMPER")
    return "REPLAY_MATCH"
