from .errors import Refused
def transport_graph(nodes,edges):
    g={n:[] for n in nodes}
    for a,b in edges:
        if a not in g or b not in g: raise Refused("REFUSED[UNKNOWN_TRANSPORT_NODE]")
        g[a].append(b)
    seen=set(); active=set()
    def visit(n):
        if n in active: raise Refused("REFUSED[CYCLIC_TRANSPORT_PROOF]")
        if n in seen:return
        active.add(n)
        for p in g[n]:visit(p)
        active.remove(n);seen.add(n)
    for n in sorted(g):visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(g.items())}
