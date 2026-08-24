from .errors import Refused
def blockers(graph,standings):
    hard={'BUILD_BROKEN','BLOCKED'}; visiting=set(); done=set(); found=set()
    def visit(n):
        if n in visiting: raise Refused('DEPENDENCY_CYCLE',n)
        if n in done:return
        visiting.add(n)
        if standings.get(n) in hard: found.add(n)
        for d in graph.get(n,()): visit(d)
        visiting.remove(n); done.add(n)
    for n in graph: visit(n)
    return frozenset(found)
