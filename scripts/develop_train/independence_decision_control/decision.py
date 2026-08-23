from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .beta import BetaEvidence
from .loss import LossMatrix


class Decision(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    DEPENDENT = "DEPENDENT"
    DEFER = "DEFER"


@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    risk: Fraction
    risks: tuple


def decide(evidence: BetaEvidence, loss: LossMatrix):
    p = evidence.mean_independent
    q = 1 - p
    risks = (
        (Decision.INDEPENDENT, q * loss.false_independent),
        (Decision.DEPENDENT, p * loss.false_dependent),
        (Decision.DEFER, loss.defer),
    )
    decision, risk = min(risks, key=lambda item: (item[1], item[0].value))
    return DecisionResult(decision, risk, risks)
