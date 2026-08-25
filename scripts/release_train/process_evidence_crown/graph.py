from dataclasses import dataclass
from .evidence import EvidenceNode
from .refusal import Refused

@dataclass
class EvidenceGraph:
    nodes: dict[str,EvidenceNode]
    parents: dict[str,tuple[str,...]]
    def __post_init__(self):
        if set(self.parents)-set(self.nodes): raise Refused("UNKNOWN_EVIDENCE_NODE")
        for child,ps in self.parents.items():
            if child in ps or any(p not in self.nodes for p in ps): raise Refused("INVALID_EVIDENCE_EDGE")
        self.order()
    def order(self):
        indeg={n:0 for n in self.nodes}; children={n:[] for n in self.nodes}
        for c,ps in self.parents.items():
            indeg[c]+=len(ps)
            for p in ps: children[p].append(c)
        q=sorted(n for n,d in indeg.items() if d==0); out=[]
        while q:
            n=q.pop(0); out.append(n)
            for c in sorted(children[n]):
                indeg[c]-=1
                if indeg[c]==0: q.append(c); q.sort()
        if len(out)!=len(self.nodes): raise Refused("CYCLIC_EVIDENCE_GRAPH")
        return tuple(out)
    def closure(self, ids):
        need=set(ids); stack=list(ids)
        while stack:
            x=stack.pop()
            for p in self.parents.get(x,()):
                if p not in need: need.add(p); stack.append(p)
        return tuple(n for n in self.order() if n in need)
