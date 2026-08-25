from .refusal import Refused
REQUIRED=frozenset({'NODE_DOWN','PARTITION','LATENCY','LOSS','VERSION_SKEW','CERTIFICATE','AMBIGUOUS_DO'})
def require_failure_worlds(worlds:dict[str,str]):
    missing=REQUIRED-set(worlds)
    if missing: raise Refused("INCOMPLETE_FAILURE_WORLD_COVERAGE", ','.join(sorted(missing)))
    bad=sorted(k for k,v in worlds.items() if k in REQUIRED and v not in {'PASS','REFUSED'})
    if bad: raise Refused("UNRESOLVED_FAILURE_WORLD", ','.join(bad))
    return True
