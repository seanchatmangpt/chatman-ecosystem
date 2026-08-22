from dataclasses import dataclass
from hashlib import sha256
import json
from .realization import STRATEGIES
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class Policy:
    generation:int
    exploration:float
    min_support:int
    max_cost:float
    max_latency_ms:float
    max_failure_rate:float
    def __post_init__(self):
        if self.generation<0 or self.min_support<1 or not 0<=self.exploration<=1 or self.max_cost<0 or self.max_latency_ms<0 or not 0<=self.max_failure_rate<=1: raise Refusal("REFUSED_INVALID_POLICY")
    @property
    def digest(self):
        body={"generation":self.generation,"exploration":self.exploration,"min_support":self.min_support,"max_cost":self.max_cost,"max_latency_ms":self.max_latency_ms,"max_failure_rate":self.max_failure_rate,"strategies":STRATEGIES}
        return sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
