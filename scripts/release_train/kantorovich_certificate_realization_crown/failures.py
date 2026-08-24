from .refusal import Refused
REQUIRED=frozenset({'node','partition','latency','loss','version','certificate','ambiguous-do'})
def require(observations):
    missing=REQUIRED-{o.world for o in observations}
    if missing: raise Refused('MISSING_FAILURE_WORLDS:'+','.join(sorted(missing)))
    return True
