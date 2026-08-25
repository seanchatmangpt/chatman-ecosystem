from .errors import Refused
REQUIRED=frozenset({'DISCOVERY','CONFORMANCE','SIMULATION','PREDICTION','OPTIMIZATION','INTERVENTION','MONITORING','OBJECT_CENTRIC','EVENT_CENTRIC','DECLARATIVE','PROCEDURAL'})
def require_methodologies(observed):
    missing=REQUIRED-set(observed)
    if missing: raise Refused('INCOMPLETE_METHODOLOGY_CLOSURE',','.join(sorted(missing)))
    return True
