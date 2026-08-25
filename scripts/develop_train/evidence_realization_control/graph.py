from collections import defaultdict, deque
from .errors import Refused
class EvidenceGraph:
    def __init__(self,nodes,edges):
        nodes=tuple(nodes)
        self.nodes={n.evidence_id:n for n in nodes}; self.edges=tuple(edges)
        if len(self.nodes)!=len(nodes): raise Refused('REFUSED[DUPLICATE_EVIDENCE]')
        for a,b in self.edges:
            if a not in self.nodes or b not in self.nodes: raise Refused('REFUSED[UNKNOWN_DEPENDENCY]')
        self.order=self._topo()
    def _topo(self):
        indeg={k:0 for k in self.nodes}; out=defaultdict(list)
        for a,b in self.edges: out[a].append(b); indeg[b]+=1
        q=deque(sorted(k for k,v in indeg.items() if v==0)); order=[]
        while q:
            x=q.popleft(); order.append(x)
            for y in sorted(out[x]):
                indeg[y]-=1
                if indeg[y]==0:q.append(y)
        if len(order)!=len(self.nodes): raise Refused('REFUSED[CYCLIC_EVIDENCE_GRAPH]')
        return tuple(order)
