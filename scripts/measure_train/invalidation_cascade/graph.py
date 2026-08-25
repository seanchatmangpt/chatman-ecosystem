from .subject import Refused

def build_graph(bindings):
    nodes=set()
    edges={}
    for b in bindings:
        nodes.add(b.consumer); nodes.add(b.producer)
        edges.setdefault(b.producer, []).append(b.consumer)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in done: return
        visiting.add(n)
        for c in edges.get(n, ()): visit(c)
        visiting.remove(n); done.add(n)
    for n in nodes: visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(edges.items(), key=lambda kv:(kv[0].repo,kv[0].sha))}
