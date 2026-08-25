from .refusal import Refused
BAD={"BUILD_BROKEN","BLOCKED","UNSUPPORTED"}
def blockers(graph,standing):
    out=set(); visiting=set(); done=set()
    def walk(n):
        if n in visiting: raise Refused("DEPENDENCY_CYCLE",n)
        if n in done:return
        visiting.add(n)
        if standing.get(n) in BAD: out.add(n)
        for d in graph.get(n,()): walk(d)
        visiting.remove(n);done.add(n)
    for n in graph: walk(n)
    return frozenset(out)
