from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .admission import admit_attempt
from .attempt import RecoveryAttempt
from .authority import ActionClass, require
from .context import RecoveryContext
from .dependency import DependencyGraph
from .persistence import PersistenceNeed, select
from .receipt import QualificationReceipt
from .recovery import RecoveryStrategy, decide
from .witness import CompatibilityWitness

@dataclass(frozen=True)
class Qualification:
    standing: str
    reason: str
    receipt: QualificationReceipt

def qualify(*, attempt: RecoveryAttempt, current: RecoveryContext, witness: CompatibilityWitness | None, strategy: RecoveryStrategy, graph: DependencyGraph, standings: dict[str, str], persistence: PersistenceNeed, now: datetime, parent_digest: str | None = None) -> Qualification:
    require(ActionClass.CONSTRUCT)
    admit_attempt(attempt, current, witness, now)
    decision = decide(strategy, attempt, witness)
    blockers = graph.blockers(attempt.consumer, standings)
    standing = "BLOCKED" if blockers else decision.standing
    reason = "dependency blockers" if blockers else decision.reason
    receipt = QualificationReceipt(consumer=attempt.consumer, attempt_id=attempt.attempt_id, current_context_digest=current.digest, strategy=strategy.value, standing=standing, blockers=blockers, store=select(persistence).value, parent_digest=parent_digest)
    return Qualification(standing, reason, receipt)
