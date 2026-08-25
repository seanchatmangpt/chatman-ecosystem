from .refusal import Refused
REQUIRED=frozenset({'discovery','conformance','simulation','prediction','optimization','intervention','monitoring','event-centric','object-centric','declarative','procedural'})
def require(observations):
    missing=REQUIRED-{o.methodology for o in observations}
    if missing: raise Refused('MISSING_METHODOLOGIES:'+','.join(sorted(missing)))
    return True
