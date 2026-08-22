from dataclasses import dataclass
from datetime import datetime
from .context import RecoveryContext
from .subject import Refused

KINDS={"EXACT","SEMANTIC_EQUIVALENT","BACKWARD_COMPATIBLE"}
RESULTS={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class CompatibilityWitness:
    before: RecoveryContext
    after: RecoveryContext
    kind: str
    result: str
    witness_id: str
    observed_at: datetime
    before_fingerprint: str
    after_fingerprint: str
    def __post_init__(self):
        if self.kind not in KINDS: raise Refused("REFUSED[UNKNOWN_WITNESS_KIND]")
        if self.result not in RESULTS: raise Refused("REFUSED[INVALID_WITNESS_RESULT]")
        if not self.witness_id.strip(): raise Refused("REFUSED[EMPTY_WITNESS_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_WITNESS_TIME]")
        for v in (self.before_fingerprint,self.after_fingerprint):
            if len(v)!=64 or any(c not in "0123456789abcdef" for c in v):
                raise Refused("REFUSED[INVALID_CONTEXT_FINGERPRINT]")
        if self.kind=="EXACT" and self.before_fingerprint != self.after_fingerprint:
            raise Refused("REFUSED[FALSE_EXACT_WITNESS]")
