from __future__ import annotations
from dataclasses import dataclass
from .information import InformationContribution
from .subject import Refusal
@dataclass(frozen=True,slots=True)
class SequentialDecision:
    statistic:float; result:str
def decide(contributions:tuple[InformationContribution,...],*,accept_at:float=2.0,reject_at:float=-2.0)->SequentialDecision:
    if reject_at>=accept_at: raise Refusal("REFUSED[INVALID_SEQUENTIAL_THRESHOLDS]")
    statistic=sum(c.value for c in contributions)
    result="ACCEPT_BOUNDED" if statistic>=accept_at else "REJECT" if statistic<=reject_at else "CONTINUE"
    return SequentialDecision(statistic,result)
