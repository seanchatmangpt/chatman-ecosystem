from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class EvidenceNode:
    evidence_id: str
    parents: tuple[str,...]
    implementation_digest: str
    model_digest: str
    domain: str
    root: str
    def __post_init__(self):
        if not self.evidence_id or not self.domain or not self.root:
            raise Refused("REFUSED[INVALID_EVIDENCE_PROVENANCE]")
        if len(self.implementation_digest)!=64 or len(self.model_digest)!=64:
            raise Refused("REFUSED[INVALID_PROVENANCE_DIGEST]")
def admit_graph(nodes):
    rows=tuple(nodes); by={n.evidence_id:n for n in rows}
    if len(by)!=len(rows): raise Refused("REFUSED[DUPLICATE_EVIDENCE_NODE]")
    for n in rows:
        if any(p not in by for p in n.parents): raise Refused("REFUSED[MISSING_EVIDENCE_PARENT]")
    visiting=set(); done=set()
    def visit(x):
        if x in visiting: raise Refused("REFUSED[CYCLIC_EVIDENCE_GRAPH]")
        if x in done: return
        visiting.add(x)
        for p in by[x].parents: visit(p)
        visiting.remove(x); done.add(x)
    for x in sorted(by): visit(x)
    return by
def ancestors(node_id, graph):
    seen=set()
    def walk(x):
        for p in graph[x].parents:
            if p not in seen:
                seen.add(p); walk(p)
    walk(node_id); return frozenset(seen)
def require_independent(left,right,graph):
    a,b=graph[left],graph[right]
    if left==right: raise Refused("REFUSED[SELF_INDEPENDENCE]")
    if a.implementation_digest==b.implementation_digest or a.model_digest==b.model_digest or a.domain==b.domain:
        raise Refused("REFUSED[PROVENANCE_ALIAS]")
    if ancestors(left,graph) & ancestors(right,graph):
        raise Refused("REFUSED[SHARED_EVIDENCE_ANCESTRY]")
    return True
