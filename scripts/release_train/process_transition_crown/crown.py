from dataclasses import dataclass
from .obligation import State

REQUIRED_OBLIGATIONS=("methodology","powl","reactor","multi_engine","event_object_oracle","multi_region_tls","failure_world","brce","receipt_replay","exact_head","broad_ci","repository_crown")

@dataclass(frozen=True)
class CrownStanding:
    state: State
    missing: tuple[str,...]
    failed: tuple[str,...]
    blocked: tuple[str,...]

def compute(states:dict[str,State]) -> CrownStanding:
    missing=tuple(k for k in REQUIRED_OBLIGATIONS if k not in states or states[k] in {State.UNKNOWN,State.UNSUPPORTED})
    failed=tuple(k for k,v in states.items() if k in REQUIRED_OBLIGATIONS and v==State.BUILD_BROKEN)
    blocked=tuple(k for k,v in states.items() if k in REQUIRED_OBLIGATIONS and v==State.BLOCKED)
    if failed:return CrownStanding(State.BUILD_BROKEN,missing,failed,blocked)
    if blocked:return CrownStanding(State.BLOCKED,missing,failed,blocked)
    if missing:return CrownStanding(State.UNKNOWN,missing,failed,blocked)
    if all(states[k]==State.ALIVE for k in REQUIRED_OBLIGATIONS): return CrownStanding(State.ALIVE,(),(),())
    return CrownStanding(State.PARTIAL_ALIVE,missing,failed,blocked)
