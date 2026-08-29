from dataclasses import dataclass
from enum import Enum
from .probability import nonnegative
from .pareto import frontier

class Strategy(str,Enum):
    MIN_EXPECTED_LOSS='MIN_EXPECTED_LOSS'; MIN_FALSE_PRECISION='MIN_FALSE_PRECISION'; MAX_INFORMATION='MAX_INFORMATION'; MIN_EVIDENCE_COST='MIN_EVIDENCE_COST'
@dataclass(frozen=True)
class Candidate:
    name:str; expected_loss:object; false_precision_risk:object; evidence_cost:object; information_gain:object
    def __post_init__(self):
        for n in ('expected_loss','false_precision_risk','evidence_cost','information_gain'): object.__setattr__(self,n,nonnegative(getattr(self,n)))
def select(candidates,strategy):
    fs=frontier(candidates)
    if strategy==Strategy.MIN_EXPECTED_LOSS: return min(fs,key=lambda c:(c.expected_loss,c.name))
    if strategy==Strategy.MIN_FALSE_PRECISION: return min(fs,key=lambda c:(c.false_precision_risk,c.name))
    if strategy==Strategy.MAX_INFORMATION: return max(fs,key=lambda c:(c.information_gain,c.name))
    return min(fs,key=lambda c:(c.evidence_cost,c.name))
