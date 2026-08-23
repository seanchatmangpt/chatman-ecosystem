from dataclasses import dataclass
from .refusal import refuse

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict
    standing: dict
    def order(self,root):
        seen=set(); active=set(); out=[]
        def visit(n):
            if n in active: refuse("DEPENDENCY_CYCLE")
            if n in seen: return
            active.add(n)
            for d in self.edges.get(n,()): visit(d)
            active.remove(n); seen.add(n); out.append(n)
        visit(root); return tuple(out)
    def blockers(self,root):
        order=self.order(root); bad={"BUILD_BROKEN","BLOCKED"}
        return tuple(n for n in order if self.standing.get(n) in bad)
