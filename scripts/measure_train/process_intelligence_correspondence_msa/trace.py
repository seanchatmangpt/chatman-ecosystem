from .subject import Refused
def trace_equivalence(rails, required_kinds=()):
    rows=tuple(rails)
    bykind={k:[r for r in rows if r.kind==k] for k in required_kinds}
    missing=[k for k,v in bykind.items() if not v]
    if missing: raise Refused("REFUSED[MISSING_REQUIRED_RAIL:"+",".join(sorted(missing))+"]")
    passing=[r for r in rows if r.state=="PASS"]
    if not passing: return "UNKNOWN"
    digests={r.trace_digest for r in passing}
    return "EQUIVALENT" if len(digests)==1 else "DIVERGENT"
