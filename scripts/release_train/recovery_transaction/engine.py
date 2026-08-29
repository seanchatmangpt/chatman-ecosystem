from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .admission import admit_attempt
from .attempt import RecoveryAttempt
from .authority import ActionClass, require
from .context import RecoveryContext
from .dependency import DependencyGraph
from .idempotency import IdempotencyLedger
from .persistence import PersistenceNeed, select_store
from .receipt import Receipt
from .strategy import decide
from .transitions import ContextTransition, require_no_aba
from .witness import CompatibilityWitness
@dataclass(frozen=True)
class Qualification:
    standing:str; reason:str; store:str; phases:tuple[str,...]; receipt:Receipt

def qualify(*, attempt:RecoveryAttempt,current:RecoveryContext,witness:CompatibilityWitness|None,strategy:str,at:datetime,transitions:list[ContextTransition],graph:DependencyGraph,root:str,standings:dict[str,str],need:PersistenceNeed,ledger:IdempotencyLedger)->Qualification:
    require(ActionClass.SELECT); require_no_aba(transitions); admit_attempt(attempt,current,witness,at,strategy)
    decision=decide(strategy,witness); blockers=graph.blockers(root,standings); standing="BLOCKED" if blockers else decision.standing
    reason="DEPENDENCY_BLOCKER" if blockers else "RECOVERY_REQUIRES_VERIFY"
    store=select_store(need).value; phases=("VERIFY","CONSTRUCT")
    body={"attempt_id":attempt.attempt_id,"consumer":attempt.consumer.exact_id,"current_context":current.digest,"strategy":strategy,"standing":standing,"reason":reason,"blockers":list(blockers),"store":store,"phases":list(phases)}
    receipt=Receipt.make(body); ledger.admit(attempt.attempt_id,receipt.digest); require(ActionClass.CONSTRUCT)
    return Qualification(standing,reason,store,phases,receipt)
