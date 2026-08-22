from __future__ import annotations
from enum import Enum
from .frontier import ConsumerState

class CompletionStrategy(str,Enum):
    ALL="ALL"; QUORUM="QUORUM"; CRITICAL_PATH="CRITICAL_PATH"

_POSITIVE={"REQUALIFIED","UNSUPPORTED"}

def complete(states:tuple[ConsumerState,...], strategy:CompletionStrategy, critical:frozenset[str]=frozenset())->bool:
    if not states: return False
    good={s.consumer for s in states if s.state in _POSITIVE}
    if strategy is CompletionStrategy.ALL: return len(good)==len(states)
    if strategy is CompletionStrategy.QUORUM: return len(good) >= (len(states)//2 + 1)
    if not critical: raise ValueError("REFUSED[MISSING_CRITICAL_PATH]")
    consumers={s.consumer for s in states}
    if not critical <= consumers: raise ValueError("REFUSED[UNKNOWN_CRITICAL_CONSUMER]")
    return critical <= good
