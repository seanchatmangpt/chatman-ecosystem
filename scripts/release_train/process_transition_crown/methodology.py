from .refusal import Refused

REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event_centric","object_centric","declarative","procedural"})

def require_methods(methods:set[str]) -> frozenset[str]:
    unknown=set(methods)-REQUIRED
    if unknown: raise Refused("UNKNOWN_METHODOLOGY",",".join(sorted(unknown)))
    missing=REQUIRED-set(methods)
    if missing: raise Refused("METHODOLOGY_INCOMPLETE",",".join(sorted(missing)))
    return REQUIRED
