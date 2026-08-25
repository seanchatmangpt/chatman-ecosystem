from .refusal import Refused
BAD={"BLOCKED","BUILD_BROKEN","UNSUPPORTED"}
def blockers(graph,standing):
    visiting=set(); done={}
    def walk(n):
        if n in visiting: raise Refused("DEPENDENCY_CYCLE",n)
        if n in done: return done[n]
        visiting.add(n); out=set()
        if standing.get(n) in BAD: out.add(n)
        for d in graph.get(n,()): out |= walk(d)
        visiting.remove(n); done[n]=out; return out
    return {n:frozenset(walk(n)) for n in graph}
