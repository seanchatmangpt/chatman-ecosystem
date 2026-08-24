from .refusal import refuse
REQUIRED=frozenset(["SEMANTIC","POWL","REACTOR","BEAM","PLAN","WASM","NIF","REMOTE","BRCE"])
def require_rails(evidence):
    missing=REQUIRED-set(evidence)
    if missing:
        refuse("MISSING_RAILS", ",".join(sorted(missing)))
    values={evidence[name] for name in REQUIRED}
    if len(values)!=1:
        refuse("RAIL_DIVERGENCE")
    return next(iter(values))
