from __future__ import annotations
from .refusal import Refused

REQUIRED = frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event-centric","object-centric","declarative","procedural"})

def require_complete(observed: set[str]) -> None:
    missing = REQUIRED - observed
    unknown = observed - REQUIRED
    if unknown:
        raise Refused("UNKNOWN_METHODOLOGY", ",".join(sorted(unknown)))
    if missing:
        raise Refused("INCOMPLETE_METHODOLOGY_COVERAGE", ",".join(sorted(missing)))
