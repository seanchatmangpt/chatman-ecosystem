from dataclasses import dataclass
from .errors import Refused
REQUIRED=frozenset({"node_down","partition","latency","loss","version_skew","certificate","ambiguous_do"})
@dataclass(frozen=True)
class FailureWorld:
    covered:frozenset[str]
    def require_complete(self):
        missing=REQUIRED-self.covered
        if missing: raise Refused("REFUSED[INCOMPLETE_FAILURE_WORLD]:"+",".join(sorted(missing)))
        return True
