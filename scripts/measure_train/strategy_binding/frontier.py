import hashlib, json
from .subject import Refused

def canonical_frontier(candidates):
    by_id={}
    for c in candidates:
        old=by_id.get(c.cut_id)
        if old and old!=c: raise Refused("REFUSED[DIVERGENT_CUT_IDENTITY]")
        by_id[c.cut_id]=c
    ordered=tuple(sorted(by_id.values()))
    raw=json.dumps([{"id":c.cut_id,"g":c.generation,"p":sorted(c.producer_generations),"t":c.observed_at.isoformat(),"complete":c.complete} for c in ordered],sort_keys=True,separators=(",",":"))
    return ordered, hashlib.sha256(raw.encode()).hexdigest()
