from .refusal import Refused
REQUIRED=frozenset({'SEMANTIC','POWL','REACTOR','BEAM','PLAN','WASM','NIF','REMOTE','BRCE'})
def require_rails(rails:dict[str,str]):
    missing=REQUIRED-set(rails)
    if missing: raise Refused("INCOMPLETE_REFERENCE_RAILS", ','.join(sorted(missing)))
    failed=sorted(k for k,v in rails.items() if k in REQUIRED and v!='PASS')
    if failed: raise Refused("REFERENCE_RAIL_NOT_ALIVE", ','.join(failed))
    return True
