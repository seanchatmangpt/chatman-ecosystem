from .errors import Refused
REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","object-centric","event-centric","declarative","procedural"})
def require_methodologies(observed):
    missing=REQUIRED-set(observed)
    if missing: raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE", ",".join(sorted(missing)))
    return True
