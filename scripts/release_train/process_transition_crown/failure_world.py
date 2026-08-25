from dataclasses import dataclass
from .refusal import Refused

REQUIRED=frozenset({"node_down","partition","latency","loss","version_skew","certificate","ambiguous_do"})

@dataclass(frozen=True)
class FailureWorld:
    observed: frozenset[str]

    def require_complete(self):
        missing=REQUIRED-self.observed
        if missing: raise Refused("INCOMPLETE_FAILURE_WORLD", ",".join(sorted(missing)))
        return self
