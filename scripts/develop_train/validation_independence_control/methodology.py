from .errors import Refused
REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event_centric","object_centric","declarative","procedural"})
def require_methodologies(values):
    missing=REQUIRED-set(values)
    if missing: raise Refused("INCOMPLETE_METHODOLOGY", ",".join(sorted(missing)))
    return True
