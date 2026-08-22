from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib,json
from .epoch import InvalidationEpoch

@dataclass(frozen=True,slots=True)
class QualificationReceipt:
    schema:str; producer:str; generation:int; event_id:str; strategy:str; standing:str; store:str; frontier:tuple[dict,...]; actuation_performed:bool; digest:str

def _payload(epoch, strategy, standing, store, frontier):
    return {"schema":"chatman.develop-epoch-discharge/1","producer":epoch.producer.value,"generation":epoch.generation,"event_id":epoch.event_id,"strategy":strategy,"standing":standing,"store":store,"frontier":frontier,"actuation_performed":False}
def make_receipt(epoch:InvalidationEpoch,strategy:str,standing:str,store:str,frontier:tuple[dict,...])->QualificationReceipt:
    p=_payload(epoch,strategy,standing,store,frontier); raw=json.dumps(p,sort_keys=True,separators=(",",":")); digest=hashlib.sha256(raw.encode()).hexdigest()
    return QualificationReceipt(**p,digest=digest)
def replay(receipt:QualificationReceipt)->bool:
    p=asdict(receipt); digest=p.pop("digest")
    if p.get("actuation_performed") is not False: return False
    raw=json.dumps(p,sort_keys=True,separators=(",",":")); return hashlib.sha256(raw.encode()).hexdigest()==digest
