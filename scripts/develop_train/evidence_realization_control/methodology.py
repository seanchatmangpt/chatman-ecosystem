from .errors import Refused
REQUIRED=frozenset({'discovery','conformance','simulation','prediction','optimization','intervention','monitoring','event_centric','object_centric','declarative','procedural'})
def require_closure(observed):
    missing=REQUIRED-set(observed)
    if missing: raise Refused('REFUSED[INCOMPLETE_METHODOLOGY:'+','.join(sorted(missing))+']')
    return True
