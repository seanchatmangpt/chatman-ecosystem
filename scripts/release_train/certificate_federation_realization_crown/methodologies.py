from .refusal import Refused
REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event-centric","object-centric","declarative","procedural"})

def require_methodologies(observed) -> frozenset[str]:
    got=frozenset(observed)
    missing=REQUIRED-got
    if missing: raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE", ",".join(sorted(missing)))
    return got
