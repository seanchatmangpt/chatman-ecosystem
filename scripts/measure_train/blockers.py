from __future__ import annotations
from dataclasses import dataclass
from .identity import Subject, Standing, Refused, RefusalCode

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[Subject, tuple[Subject,...]]
    def order(self)->tuple[Subject,...]:
        visiting=set(); done=set(); out=[]
        def visit(n):
            if n in visiting: raise Refused(RefusalCode.DEPENDENCY_CYCLE,n.identity)
            if n in done: return
            visiting.add(n)
            for d in sorted(self.edges.get(n,())): visit(d)
            visiting.remove(n); done.add(n); out.append(n)
        for n in sorted(self.edges): visit(n)
        return tuple(out)

def propagate(graph: DependencyGraph, standings: dict[Subject,Standing])->dict[Subject,Standing]:
    out=dict(standings)
    for n in graph.order():
        deps=graph.edges.get(n,())
        if any(out.get(d,Standing.UNKNOWN) in (Standing.BUILD_BROKEN,Standing.BLOCKED) for d in deps): out[n]=Standing.BLOCKED
        elif any(out.get(d,Standing.UNKNOWN)==Standing.UNKNOWN for d in deps) and out.get(n)!=Standing.BUILD_BROKEN: out[n]=Standing.UNKNOWN
    return out
