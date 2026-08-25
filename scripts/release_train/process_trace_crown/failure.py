from __future__ import annotations
from enum import Enum
from .refusal import Refused

class Failure(str, Enum):
    NODE_DOWN="NODE_DOWN"; PARTITION="PARTITION"; LATENCY="LATENCY"; LOSS="LOSS"; VERSION_SKEW="VERSION_SKEW"; CERTIFICATE="CERTIFICATE"; AMBIGUOUS_DO="AMBIGUOUS_DO"

REQUIRED_FAILURES = frozenset(Failure)

def require_complete(observed: set[Failure]) -> None:
    missing = REQUIRED_FAILURES - observed
    if missing:
        raise Refused("INCOMPLETE_FAILURE_WORLD", ",".join(sorted(x.value for x in missing)))
