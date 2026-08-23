from dataclasses import dataclass
from datetime import datetime
from .authority import ActionClass, admit_action
from .conflict import classify
from .errors import Refused
from .merkle import merkle_root
from .quorum import qualified
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    receipt: Receipt | None

class ReplicatedEvidenceEngine:
    def qualify(self, states, lease, now: datetime, action: ActionClass = ActionClass.CONSTRUCT) -> Qualification:
        admit_action(action)
        states=list(states)
        if not lease.admits(now): raise Refused("STALE_REPLICA_LEASE")
        if classify(states)=="SPLIT_BRAIN": return Qualification("UNKNOWN", None)
        ok, value=qualified(states)
        if not ok: return Qualification("UNKNOWN", None)
        generation=max(s.generation for s in states)
        current=[s for s in states if s.generation==generation and s.value_digest==value]
        root=merkle_root([s.digest() for s in current])
        receipt=Receipt(current[0].subject,generation,value,root,"PARTIAL_ALIVE",False)
        return Qualification("PARTIAL_ALIVE",receipt)
