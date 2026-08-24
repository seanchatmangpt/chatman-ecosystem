from .refusal import Refused
REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event_centric","object_centric","declarative","procedural"})
def require_methods(methods):
    missing=REQUIRED-set(methods)
    if missing: raise Refused("METHODOLOGY_GAP",",".join(sorted(missing)))
    return True
