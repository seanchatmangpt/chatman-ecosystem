from dataclasses import dataclass,asdict
import hashlib,json
from .refusal import Refused
@dataclass(frozen=True)
class Receipt:
    schema:str; subject:str; standing:str; evidence_digest:str; authority:str; actuation_performed:bool; digest:str
def make(subject,standing,evidence_digest,authority="SELECT"):
    if authority=="DO": raise Refused("RECEIPT_DO_FORBIDDEN")
    body={"schema":"chatman.kantorovich-dual-crown/1","subject":subject,"standing":standing,"evidence_digest":evidence_digest,"authority":authority,"actuation_performed":False}
    d=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Receipt(**body,digest=d)
def replay(r):
    body=asdict(r); got=body.pop("digest")
    if body.get("actuation_performed") or body.get("authority")=="DO": raise Refused("REPLAY_AUTHORITY_DRIFT")
    want=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    if got!=want: raise Refused("RECEIPT_TAMPER")
    return "REPLAY_MATCH"
