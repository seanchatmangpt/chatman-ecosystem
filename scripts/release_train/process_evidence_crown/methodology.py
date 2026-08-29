from .refusal import Refused
REQUIRED=frozenset({'DISCOVERY','CONFORMANCE','SIMULATION','PREDICTION','OPTIMIZATION','INTERVENTION','MONITORING','EVENT_CENTRIC','OBJECT_CENTRIC','DECLARATIVE','PROCEDURAL'})
def require_methodologies(observed):
    missing=REQUIRED-set(observed)
    if missing: raise Refused("INCOMPLETE_PROCESS_METHODOLOGY", ','.join(sorted(missing)))
    return True
