from .subject import Refused
def admit_graph(nodes, edges):
    ids={n.evidence_id for n in nodes}
    if len(ids)!=len(tuple(nodes)): raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
    g={i:[] for i in ids}
    for child,parent in edges:
        if child not in g or parent not in g: raise Refused("REFUSED[UNKNOWN_EVIDENCE_DEPENDENCY]")
        g[child].append(parent)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting: raise Refused("REFUSED[CYCLIC_EVIDENCE_GRAPH]")
        if n in done: return
        visiting.add(n)
        for p in g[n]: visit(p)
        visiting.remove(n); done.add(n)
    for n in sorted(g): visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(g.items())}
