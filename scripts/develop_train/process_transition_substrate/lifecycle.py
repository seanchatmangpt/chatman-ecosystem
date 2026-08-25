from dataclasses import dataclass
from .obligation import Obligation, State
from .errors import Refused
@dataclass(frozen=True)
class Discharge:
    key: str
    proof_digest: str
    source: str
    def __post_init__(self):
        if len(self.proof_digest)!=64: raise Refused("REFUSED[PROOF_REQUIRED]")
@dataclass(frozen=True)
class Regression:
    key: str
    before: State
    after: State
    severity: int
    def __post_init__(self):
        if self.before != State.PASS or self.after == State.PASS: raise Refused("REFUSED[NOT_REGRESSION]")
        if self.severity < 1: raise Refused("REFUSED[INVALID_SEVERITY]")
def classify(before: Obligation, after: Obligation, proof_digest: str|None=None):
    if before.key != after.key: raise Refused("REFUSED[OBLIGATION_DRIFT]")
    if before.state != State.PASS and after.state == State.PASS:
        if proof_digest is None: raise Refused("REFUSED[DISCHARGE_PROOF_REQUIRED]")
        return Discharge(after.key, proof_digest, after.source)
    if before.state == State.PASS and after.state != State.PASS:
        severity={State.FAIL:3,State.REFUSED:3,State.BLOCKED:2,State.UNKNOWN:1,State.UNSUPPORTED:1}.get(after.state,1)
        return Regression(after.key,before.state,after.state,severity)
    return None
