from .refusal import Refused
class DependencyGraph:
    def __init__(self, edges): self.edges={k:tuple(v) for k,v in edges.items()}
    def order(self):
        seen=set(); active=set(); out=[]
        def visit(n):
            if n in active: raise Refused("CYCLIC_DEPENDENCY")
            if n in seen:return
            active.add(n)
            for d in self.edges.get(n,()): visit(d)
            active.remove(n); seen.add(n); out.append(n)
        for n in sorted(self.edges): visit(n)
        return tuple(out)
    def blockers(self, states, root):
        self.order(); bad=[]
        def walk(n):
            if states.get(n) in {"BUILD_BROKEN","BLOCKED"}: bad.append(n)
            for d in self.edges.get(n,()): walk(d)
        walk(root); return tuple(sorted(set(bad)))
