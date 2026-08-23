from dataclasses import dataclass
from enum import Enum
import math
from .errors import Refused
from .rational import positive, unit

class Strategy(str, Enum):
    MAX_INFORMATION="MAX_INFORMATION"
    MAX_INDEPENDENCE="MAX_INDEPENDENCE"
    MIN_COST="MIN_COST"
    MINIMAX_LATENCY="MINIMAX_LATENCY"

@dataclass(frozen=True)
class AcquisitionCandidate:
    candidate_id: str
    expected_current_probability: object
    independence_gain: int
    cost: object
    latency_seconds: object
    def __post_init__(self):
        if not self.candidate_id: raise Refused("MISSING_ACQUISITION_CANDIDATE_ID")
        object.__setattr__(self,"expected_current_probability",unit(self.expected_current_probability))
        object.__setattr__(self,"cost",positive(self.cost)); object.__setattr__(self,"latency_seconds",positive(self.latency_seconds))
        if self.independence_gain < 0: raise Refused("NEGATIVE_INDEPENDENCE_GAIN")

def binary_entropy(p):
    p=float(unit(p))
    if p in (0.0,1.0): return 0.0
    return -p*math.log2(p)-(1-p)*math.log2(1-p)

def information_gain(candidate): return 1.0-binary_entropy(candidate.expected_current_probability)

def select(candidates,strategy):
    candidates=tuple(candidates)
    if not candidates: return None
    if strategy==Strategy.MAX_INFORMATION: return max(candidates,key=lambda c:(information_gain(c),c.independence_gain,-float(c.cost),c.candidate_id))
    if strategy==Strategy.MAX_INDEPENDENCE: return max(candidates,key=lambda c:(c.independence_gain,information_gain(c),-float(c.cost),c.candidate_id))
    if strategy==Strategy.MIN_COST: return min(candidates,key=lambda c:(float(c.cost),float(c.latency_seconds),c.candidate_id))
    if strategy==Strategy.MINIMAX_LATENCY: return min(candidates,key=lambda c:(float(c.latency_seconds),float(c.cost),c.candidate_id))
    raise Refused("UNKNOWN_ACQUISITION_STRATEGY")
