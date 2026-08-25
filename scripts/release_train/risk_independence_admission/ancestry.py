from collections import defaultdict
from .errors import Refused

class EvidenceAncestry:
    def __init__(self, edges=()):
        self.parents=defaultdict(set)
        for child,parent in edges:
            if child==parent: raise Refused('ANCESTRY_SELF_CYCLE')
            self.parents[child].add(parent)
        for n in list(self.parents): self._anc(n,set())
    def _anc(self,n,seen):
        if n in seen: raise Refused('ANCESTRY_CYCLE')
        out=set(); nxt=seen|{n}
        for p in self.parents.get(n,()): out.add(p); out |= self._anc(p,nxt)
        return out
    def ancestors(self,n): return frozenset(self._anc(n,set()))
    def shared_roots(self,a,b): return self.ancestors(a)&self.ancestors(b)
    def require_disjoint(self,a,b):
        shared=self.shared_roots(a,b)
        if shared: raise Refused('SHARED_EVIDENCE_ANCESTRY',','.join(sorted(shared)))
        return True
