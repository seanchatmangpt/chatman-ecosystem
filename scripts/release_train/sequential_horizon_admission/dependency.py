from .errors import Refused
_RED={"BLOCKED","BUILD_BROKEN","UNSUPPORTED"}
def blockers(graph,standing,root):
    seen=set(); active=set(); out=set()
    def visit(n):
        if n in active: raise Refused("DEPENDENCY_CYCLE")
        if n in seen: return
        active.add(n)
        for d in graph.get(n,()):
            if standing.get(d) in _RED: out.add(d)
            visit(d)
        active.remove(n); seen.add(n)
    visit(root); return tuple(sorted(out))
