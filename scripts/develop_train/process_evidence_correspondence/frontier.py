from .errors import Refused
def current_frontier(nodes):
    if not nodes: raise Refused("EMPTY_FRONTIER")
    g=max(n.generation for n in nodes)
    cur=[n for n in nodes if n.generation==g]
    by_kind={}
    for n in cur:
        prior=by_kind.get(n.kind)
        if prior and prior.digest!=n.digest: raise Refused("DIVERGENT_CURRENT_FRONTIER",n.kind)
        by_kind[n.kind]=n
    return g, tuple(sorted(cur,key=lambda n:n.evidence_id))
