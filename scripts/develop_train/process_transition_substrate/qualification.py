from dataclasses import dataclass
from .obligation import State
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing:str
    receipt:Receipt|None
def qualify(subject,generation,obligations,obligation_digest):
    items=list(obligations)
    states=[o.state for o in items]
    if any(s in (State.FAIL,State.REFUSED) for s in states): return Qualification("BUILD_BROKEN",None)
    if any(s==State.BLOCKED for s in states): return Qualification("BLOCKED",None)
    if any(s==State.UNKNOWN for s in states): return Qualification("UNKNOWN",None)
    r=Receipt(subject,generation,"PARTIAL_ALIVE",obligation_digest)
    return Qualification("PARTIAL_ALIVE",r)
