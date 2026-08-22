from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib, json
class CutStrategy(str, Enum):
    LATEST_COMPLETE="LATEST_COMPLETE"; MAX_FRESHNESS="MAX_FRESHNESS"; MIN_SKEW="MIN_SKEW"
@dataclass(frozen=True, slots=True)
class StrategyPolicy:
    strategy: CutStrategy
    parameters: tuple[tuple[str,str], ...]=()
    def __post_init__(self)->None:
        if len({k for k,_ in self.parameters}) != len(self.parameters): raise ValueError("REFUSED[DUPLICATE_POLICY_PARAMETER]")
    @property
    def digest(self)->str:
        body={"strategy":self.strategy.value,"parameters":sorted(self.parameters)}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
