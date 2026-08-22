from dataclasses import dataclass
from .subject import Refusal
RED={"BLOCKED","BUILD_BROKEN","REFUSED"}
@dataclass(frozen=True)
class DependencyGraph:
    edges:dict
    standing:dict
    def blockers(self,node):
        seen=set(); active=set(); out=set()
        def walk(n):
            if n in active: raise Refusal("REFUSED_DEPENDENCY_CYCLE")
            if n in seen:return
            active.add(n)
            for d in self.edges.get(n,()):
                if self.standing.get(d) in RED: out.add(d)
                walk(d)
            active.remove(n); seen.add(n)
        walk(node); return tuple(sorted(out))
