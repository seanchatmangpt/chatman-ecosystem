from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .authority import ActionClass,require
from .compatibility import CompatibilityWitness
from .dependency import DependencyGraph
from .drift import classify,DriftKind
from .frontier import CandidateFrontier
from .intent import SelectionIntent
from .persistence import PersistenceNeed,select_store
from .policy import StrategyPolicy
from .proof import SelectionProof,select
from .receipt import QualificationReceipt
from .recovery import RecoveryStrategy,recover
@dataclass(frozen=True,slots=True)
class Qualification:
    standing:str; selected_cut_id:str; receipt:QualificationReceipt; blocked:bool
def qualify(*,intent:SelectionIntent,frontier:CandidateFrontier,policy:StrategyPolicy,recovery:RecoveryStrategy,now:datetime,need:PersistenceNeed=PersistenceNeed(),witness:CompatibilityWitness|None=None,graph:DependencyGraph|None=None,standings:dict|None=None)->Qualification:
    require(ActionClass.CONSTRUCT); drift=classify(intent,policy,frontier,now)
    chosen=SelectionProof(intent).admit(frontier,policy) if drift.kind is DriftKind.EXACT else select(frontier,policy)
    decision=recover(recovery,drift.kind,witness); blocked=bool(graph is not None and standings is not None and intent.consumer in graph.blocked(standings))
    standing="BLOCKED" if blocked else decision.standing; store=select_store(need)
    receipt=QualificationReceipt(intent.consumer.coordinate,chosen.cut_id,recovery.value,policy.digest,frontier.digest,standing,store.kind.value)
    return Qualification(standing,chosen.cut_id,receipt,blocked)
