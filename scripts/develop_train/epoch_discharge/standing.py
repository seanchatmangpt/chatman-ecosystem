from __future__ import annotations
from .frontier import ConsumerState

def derive_standing(states:tuple[ConsumerState,...], is_complete:bool)->str:
    if any(s.state=="BLOCKED" for s in states): return "BLOCKED"
    if any(s.state.startswith("PENDING_") for s in states): return "UNKNOWN"
    if states and all(s.state=="UNSUPPORTED" for s in states): return "UNSUPPORTED"
    if is_complete and states: return "PARTIAL_ALIVE"
    return "UNKNOWN"
