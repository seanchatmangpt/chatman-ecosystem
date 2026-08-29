import hashlib, json
from dataclasses import dataclass
from .subject import Refusal

_ALLOWED = {'LATEST_COMPLETE','MAX_FRESHNESS','MIN_SKEW'}
@dataclass(frozen=True)
class StrategyPolicy:
    strategy: str
    parameters: tuple[tuple[str,str], ...] = ()
    def __post_init__(self):
        if self.strategy not in _ALLOWED:
            raise Refusal('REFUSED[UNKNOWN_SELECTION_STRATEGY]')
        keys=[k for k,_ in self.parameters]
        if len(keys)!=len(set(keys)):
            raise Refusal('REFUSED[DUPLICATE_POLICY_PARAMETER]')
    @property
    def digest(self):
        body={'strategy':self.strategy,'parameters':sorted(self.parameters)}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
