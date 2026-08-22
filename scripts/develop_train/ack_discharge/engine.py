from dataclasses import dataclass
import hashlib,json
from .authority import ActionClass,require_nonconsequential
from .persistence import select
from .receipt import QualificationReceipt,digest
from .strategy import is_complete
@dataclass(frozen=True,slots=True)
class Qualification: complete:bool;standing:str;store:str;receipt:QualificationReceipt;receipt_digest:str
def qualify(*,producer,event,topology,frontier,strategy,requirements,evidence):
 require_nonconsequential(ActionClass.VERIFY)
 expected={node.subject.identity for node,_ in topology.affected()}
 if expected!=set(frontier.expected):raise ValueError('REFUSED[FRONTIER_TOPOLOGY_MISMATCH]')
 complete=is_complete(strategy,frontier.items());standing='PARTIAL_ALIVE' if complete else 'UNKNOWN'
 ed=hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 r=QualificationReceipt(producer.identity,event.event_id,strategy,[{'identity':i.identity,'discharged':i.discharged,'critical':i.critical} for i in frontier.items()],standing,ed,False)
 return Qualification(complete,standing,select(requirements).value,r,digest(r))
