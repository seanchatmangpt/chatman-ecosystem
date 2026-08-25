from collections import defaultdict
from .errors import Refused
class DependencyGraph:
    def __init__(self, edges=(), broken=()):
        self.parents=defaultdict(set); self.broken=set(broken)
        for child,parent in edges:
            if child==parent: raise Refused('DEPENDENCY_SELF_CYCLE')
            self.parents[child].add(parent)
        for n in list(self.parents): self._walk(n,set())
    def _walk(self,n,seen):
        if n in seen: raise Refused('DEPENDENCY_CYCLE')
        out=set(); nxt=seen|{n}
        for p in self.parents.get(n,()): out.add(p); out |= self._walk(p,nxt)
        return out
    def blockers(self,n):
        return frozenset(x for x in self._walk(n,set())|{n} if x in self.broken)
