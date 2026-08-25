from dataclasses import dataclass
from enum import Enum
from .evidence import BetaEvidence
from .loss import LossMatrix

class Decision(str, Enum):
    INDEPENDENT='INDEPENDENT'; DEPENDENT='DEPENDENT'; DEFER='DEFER'

@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    risk: object
    risks: dict

def decide(evidence: BetaEvidence, losses: LossMatrix):
    p=evidence.p_independent
    risks={
      Decision.INDEPENDENT:(1-p)*losses.false_independent,
      Decision.DEPENDENT:p*losses.false_dependent,
      Decision.DEFER:losses.defer,
    }
    order=(Decision.DEFER, Decision.DEPENDENT, Decision.INDEPENDENT)
    choice=min(order,key=lambda d:(risks[d],order.index(d)))
    return DecisionResult(choice, risks[choice], risks)
