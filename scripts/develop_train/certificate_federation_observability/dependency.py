from .errors import Refused
HARD={"BUILD_BROKEN","BLOCKED"}
def blockers(graph,standing):
    seen=set(); visiting=set()
    def visit(n):
        if n in visiting: raise Refused("DEPENDENCY_CYCLE")
        if n in seen: return
        visiting.add(n)
        for d in graph.get(n,()): visit(d)
        visiting.remove(n); seen.add(n)
    for n in sorted(graph): visit(n)
    bad={n for n,s in standing.items() if s in HARD}; changed=True
    while changed:
        changed=False
        for n,deps in graph.items():
            if n not in bad and any(d in bad for d in deps): bad.add(n); changed=True
    return frozenset(bad)
