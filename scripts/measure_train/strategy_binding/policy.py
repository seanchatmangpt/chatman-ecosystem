import hashlib, json
from dataclasses import dataclass
from .subject import Refused

STRATEGIES={"LATEST_COMPLETE","MAX_FRESHNESS","MIN_SKEW"}

@dataclass(frozen=True, order=True)
class StrategyPolicy:
    strategy:str
    parameters:tuple=()
    def __post_init__(self):
        if self.strategy not in STRATEGIES: raise Refused("REFUSED[UNKNOWN_SELECTION_STRATEGY]")
        for item in self.parameters:
            if not isinstance(item, tuple) or len(item)!=2 or not all(isinstance(x,str) for x in item):
                raise Refused("REFUSED[INVALID_STRATEGY_PARAMETER]")
    @property
    def digest(self):
        raw=json.dumps({"strategy":self.strategy,"parameters":sorted(self.parameters)},sort_keys=True,separators=(",",":"))
        return hashlib.sha256(raw.encode()).hexdigest()
