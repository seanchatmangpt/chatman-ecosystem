from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class SequentialDecision:
    statistic: float; decision: str

def decide(contributions, accept=2.0, reject=-2.0):
    if accept<=0 or reject>=0 or reject>=accept: raise Refused("REFUSED[INVALID_SEQUENTIAL_THRESHOLDS]")
    s=sum(c.value for c in contributions if c.informative)
    d="ACCEPT_BOUNDED" if s>=accept else "REJECT" if s<=reject else "CONTINUE"
    return SequentialDecision(round(s,12),d)
