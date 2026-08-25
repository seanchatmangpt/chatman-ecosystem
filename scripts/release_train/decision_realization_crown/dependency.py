from .errors import Refused
RED={"BUILD_BROKEN","BLOCKED"}
def blockers(graph,standing,root):
    visiting=set(); done=set(); out=set()
    def walk(n):
        if n in visiting: raise Refused("DEPENDENCY_CYCLE")
        if n in done: return
        visiting.add(n)
        for d in graph.get(n,()):
            if standing.get(d) in RED: out.add(d)
            walk(d)
        visiting.remove(n); done.add(n)
    walk(root)
    return tuple(sorted(out))
