from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from .subject import Refusal

class Strategy(str, Enum):
    LATEST_COMPLETE='LATEST_COMPLETE'
    MAX_FRESHNESS='MAX_FRESHNESS'
    MIN_SKEW='MIN_SKEW'

@dataclass(frozen=True)
class StrategyBinding:
    strategy: Strategy
    parameters: tuple[tuple[str, str], ...] = ()

    def fingerprint(self) -> str:
        payload={'strategy':self.strategy.value,'parameters':list(self.parameters)}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

    @classmethod
    def from_name(cls, name: str, parameters=()):
        try:
            return cls(Strategy(name), tuple(sorted(parameters)))
        except ValueError as e:
            raise Refusal('REFUSED[UNKNOWN_SELECTION_STRATEGY]') from e
