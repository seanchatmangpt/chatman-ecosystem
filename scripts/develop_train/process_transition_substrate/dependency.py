from .errors import Refused
from .obligation import State
class DependencyGraph:
    def __init__(self, edges):
        self.edges={k:tuple(v) for k,v in edges.items()}
        self._check()
    def _check(self):
        seen=set(); active=set()
        def visit(n):
            if n in active: raise Refused("REFUSED[DEPENDENCY_CYCLE]")
            if n in seen:return
            active.add(n)
            for p in self.edges.get(n,()): visit(p)
            active.remove(n); seen.add(n)
        for n in self.edges: visit(n)
    def blockers(self, states, node):
        out=set()
        def walk(n):
            for p in self.edges.get(n,()):
                if states.get(p) not in (State.PASS,State.UNSUPPORTED): out.add(p)
                walk(p)
        walk(node); return tuple(sorted(out))
