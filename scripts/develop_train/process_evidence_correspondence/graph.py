from .errors import Refused
class EvidenceGraph:
    def __init__(self,nodes):
        nodes=list(nodes)
        self.nodes={n.evidence_id:n for n in nodes}
        if len(self.nodes)!=len(nodes): raise Refused("DUPLICATE_EVIDENCE")
        for n in self.nodes.values():
            if n.evidence_id in n.parents: raise Refused("CYCLIC_EVIDENCE_GRAPH")
            for p in n.parents:
                if p not in self.nodes: raise Refused("MISSING_PARENT",p)
        self._order=self._topological()
    def _topological(self):
        incoming={k:set(v.parents) for k,v in self.nodes.items()}
        out=[]
        while incoming:
            ready=sorted(k for k,v in incoming.items() if not v)
            if not ready: raise Refused("CYCLIC_EVIDENCE_GRAPH")
            for k in ready:
                out.append(k); incoming.pop(k)
                for deps in incoming.values(): deps.discard(k)
        return tuple(out)
    @property
    def order(self): return self._order
