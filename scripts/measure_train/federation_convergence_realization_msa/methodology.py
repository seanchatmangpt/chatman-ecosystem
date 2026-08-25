from .refusals import Refused
REQUIRED={'DISCOVERY','CONFORMANCE','SIMULATION','PREDICTION','OPTIMIZATION','INTERVENTION','MONITORING','EVENT_CENTRIC','OBJECT_CENTRIC','DECLARATIVE','PROCEDURAL'}
def require_all(values):
    missing=tuple(sorted(REQUIRED-set(values)))
    if missing: raise Refused('REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]:'+','.join(missing))
    return tuple(sorted(REQUIRED))
