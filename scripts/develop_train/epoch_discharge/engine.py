from __future__ import annotations
from dataclasses import dataclass
from .epoch import InvalidationEpoch
from .witness import Witness
from .frontier import current_frontier
from .strategy import CompletionStrategy, complete
from .standing import derive_standing
from .persistence import PersistenceNeed, select_store
from .authority import ActionClass, admit_action
from .receipt import QualificationReceipt, make_receipt

@dataclass(frozen=True,slots=True)
class Qualification:
    complete:bool; standing:str; store:str; receipt:QualificationReceipt; actuation_performed:bool=False

def qualify(epoch:InvalidationEpoch, consumers:tuple[str,...], witnesses:tuple[Witness,...], strategy:CompletionStrategy, critical:frozenset[str]=frozenset(), persistence:PersistenceNeed=PersistenceNeed())->Qualification:
    admit_action(ActionClass.CONSTRUCT)
    states=current_frontier(epoch,consumers,witnesses)
    done=complete(states,strategy,critical)
    standing=derive_standing(states,done)
    store=select_store(persistence).value
    frontier=tuple({"consumer":s.consumer,"state":s.state,"result":s.result} for s in states)
    receipt=make_receipt(epoch,strategy.value,standing,store,frontier)
    return Qualification(done,standing,store,receipt,False)
