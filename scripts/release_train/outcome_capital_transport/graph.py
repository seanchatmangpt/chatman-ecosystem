from .errors import Refused

class EvidenceGraph:
    def __init__(self, nodes):
        nodes = tuple(nodes)
        self.nodes = {n.evidence_id:n for n in nodes}
        if len(self.nodes) != len(nodes):
            raise Refused("DUPLICATE_EVIDENCE")
        for node in self.nodes.values():
            for p in node.parents:
                if p not in self.nodes:
                    raise Refused("MISSING_EVIDENCE_PARENT", p)
        self._check_acyclic()

    def _check_acyclic(self):
        visiting, done = set(), set()
        def visit(k):
            if k in visiting: raise Refused("EVIDENCE_CYCLE", k)
            if k in done: return
            visiting.add(k)
            for p in self.nodes[k].parents: visit(p)
            visiting.remove(k); done.add(k)
        for k in self.nodes: visit(k)

    def ancestors(self, evidence_id):
        out=set()
        def walk(k):
            for p in self.nodes[k].parents:
                if p not in out: out.add(p); walk(p)
        walk(evidence_id)
        return frozenset(out)

    def independent_roots(self, a, b):
        aa=self.ancestors(a)|{a}; bb=self.ancestors(b)|{b}
        if aa & bb:
            raise Refused("SHARED_EVIDENCE_ANCESTRY", ",".join(sorted(aa&bb)))
        return True
