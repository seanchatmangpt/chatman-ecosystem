from .errors import Refused
def current_frontier(nodes):
    nodes=tuple(nodes)
    gens={n.generation for n in nodes}
    if not gens: raise Refused('REFUSED[EMPTY_FRONTIER]')
    g=max(gens); current=[n for n in nodes if n.generation==g]
    subjects={n.subject.key for n in current}
    if len(subjects)!=1: raise Refused('REFUSED[DIVERGENT_FRONTIER]')
    return g, tuple(sorted(current,key=lambda n:n.evidence_id))
