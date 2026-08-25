from .errors import Refused
BAD={"BUILD_BROKEN","BLOCKED"}
class DependencyGraph:
    def __init__(self, edges, standing):
        self.edges={k:tuple(v) for k,v in edges.items()}; self.standing=dict(standing); self._acyclic()
    def _acyclic(self):
        visiting=set(); done=set()
        def v(k):
            if k in visiting: raise Refused("DEPENDENCY_CYCLE", k)
            if k in done: return
            visiting.add(k)
            for d in self.edges.get(k,()): v(d)
            visiting.remove(k); done.add(k)
        for k in self.edges: v(k)
    def blockers(self, root):
        out=set()
        def walk(k):
            for d in self.edges.get(k,()):
                if self.standing.get(d,"UNKNOWN") in BAD: out.add(d)
                walk(d)
        walk(root); return tuple(sorted(out))
