from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class EvidenceNode:
    node_id: str
    parents: tuple[str, ...] = ()
    implementation: str = ""
    model: str = ""
    domain: str = ""

class EvidenceGraph:
    def __init__(self, nodes):
        source = tuple(nodes)
        self.nodes = {n.node_id: n for n in source}
        if len(self.nodes) != len(source):
            raise Refused("DUPLICATE_EVIDENCE_NODE")
        for node in self.nodes.values():
            if node.node_id in node.parents:
                raise Refused("SELF_EVIDENCE_PARENT")
            missing = set(node.parents) - self.nodes.keys()
            if missing:
                raise Refused("MISSING_EVIDENCE_PARENT", ",".join(sorted(missing)))
        self._assert_acyclic()

    def _assert_acyclic(self):
        temp, done = set(), set()
        def visit(k):
            if k in temp:
                raise Refused("CYCLIC_EVIDENCE")
            if k in done:
                return
            temp.add(k)
            for p in self.nodes[k].parents:
                visit(p)
            temp.remove(k)
            done.add(k)
        for k in sorted(self.nodes):
            visit(k)

    def ancestors(self, node_id):
        out = set()
        stack = list(self.nodes[node_id].parents)
        while stack:
            k = stack.pop()
            if k in out:
                continue
            out.add(k)
            stack.extend(self.nodes[k].parents)
        return frozenset(out)

    def disjoint(self, left, right):
        return not ((self.ancestors(left) | {left}) & (self.ancestors(right) | {right}))

def require_distinct_provenance(a: EvidenceNode, b: EvidenceNode, graph: EvidenceGraph):
    if a.node_id == b.node_id:
        raise Refused("EVIDENCE_ALIAS")
    if not all((a.implementation, a.model, a.domain, b.implementation, b.model, b.domain)):
        raise Refused("INCOMPLETE_PROVENANCE")
    if a.implementation == b.implementation or a.model == b.model or a.domain == b.domain:
        raise Refused("SHARED_PROVENANCE")
    if not graph.disjoint(a.node_id, b.node_id):
        raise Refused("SHARED_EVIDENCE_ANCESTRY")
    return True
