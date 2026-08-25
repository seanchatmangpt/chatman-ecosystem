from .errors import Refused
REQUIRED=frozenset({"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"})
def require_methodologies(observed):
    missing=sorted(REQUIRED-set(observed))
    if missing: raise Refused("INCOMPLETE_METHODOLOGY",",".join(missing))
    return True
