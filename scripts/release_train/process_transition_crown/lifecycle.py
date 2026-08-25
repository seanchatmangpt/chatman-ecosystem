from dataclasses import dataclass
from .obligation import Obligation, State
from .refusal import Refused

_SEVERITY={State.ALIVE:0,State.PARTIAL_ALIVE:1,State.UNKNOWN:2,State.UNSUPPORTED:3,State.BLOCKED:4,State.BUILD_BROKEN:5}

@dataclass(frozen=True)
class Discharge:
    key: str
    proof_source: str
    proof_digest: str
    def __post_init__(self):
        if not self.proof_source or not self.proof_digest:
            raise Refused("PROOFLESS_DISCHARGE")

@dataclass(frozen=True)
class Regression:
    key: str
    before: State
    after: State
    def __post_init__(self):
        if _SEVERITY[self.after] <= _SEVERITY[self.before]:
            raise Refused("NONREGRESSION")

def classify(before: Obligation, after: Obligation):
    if before.key != after.key:
        raise Refused("OBLIGATION_KEY_DRIFT")
    if before.state != State.ALIVE and after.state == State.ALIVE:
        return "DISCHARGE_REQUIRED"
    if _SEVERITY[after.state] > _SEVERITY[before.state]:
        return Regression(before.key,before.state,after.state)
    return "UNCHANGED_OR_IMPROVED"
