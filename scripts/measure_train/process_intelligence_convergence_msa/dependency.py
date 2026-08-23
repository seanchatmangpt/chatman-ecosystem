from .subject import Refused

def graph(nodes, edges):
    g={n:[] for n in nodes}
    for child,parent in edges:
        if child not in g or parent not in g: raise Refused("REFUSED[UNKNOWN_DEPENDENCY]")
        g[child].append(parent)
    visiting=set(); done=set()
    def visit(n):
        if n in visiting: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
        if n in done: return
        visiting.add(n)
        for p in g[n]: visit(p)
        visiting.remove(n); done.add(n)
    for n in sorted(g): visit(n)
    return {k:tuple(sorted(v)) for k,v in sorted(g.items())}
