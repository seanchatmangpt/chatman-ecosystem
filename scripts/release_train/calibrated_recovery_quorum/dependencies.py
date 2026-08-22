from .subject import Refused
class DependencyGraph:
    def __init__(self, edges): self.edges={k:tuple(v) for k,v in edges.items()}
    def order(self, root):
        out=[]; active=set(); seen=set()
        def visit(n):
            if n in active: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
            if n in seen: return
            active.add(n)
            for d in self.edges.get(n,()): visit(d)
            active.remove(n); seen.add(n); out.append(n)
        visit(root); return out
    def blockers(self,root,standing):
        return sorted(n for n in self.order(root) if standing.get(n,"UNKNOWN") in {"BUILD_BROKEN","BLOCKED"})
