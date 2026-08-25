from .subject import Refused
def current_frontier(nodes):
    by={}
    for n in nodes:
        key=(n.kind,n.domain)
        old=by.get(key)
        if old is None or n.generation>old.generation: by[key]=n
        elif n.generation==old.generation and n.evidence_id!=old.evidence_id:
            raise Refused("REFUSED[DIVERGENT_EVIDENCE_FRONTIER]")
    return tuple(sorted(by.values(), key=lambda n:(n.kind,n.domain,n.evidence_id)))
