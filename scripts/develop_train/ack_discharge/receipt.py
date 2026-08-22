from dataclasses import asdict,dataclass
import hashlib,json
from .strategy import Strategy
@dataclass(frozen=True,slots=True)
class QualificationReceipt:
 producer:str;event_id:str;strategy:Strategy;frontier:list[dict[str,object]];standing:str;evidence_digest:str;actuation_performed:bool=False
def canonical_payload(r):
 d=asdict(r);d['strategy']=r.strategy.value;return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def digest(r):return hashlib.sha256(canonical_payload(r)).hexdigest()
def replay(r,expected):return not r.actuation_performed and digest(r)==expected
