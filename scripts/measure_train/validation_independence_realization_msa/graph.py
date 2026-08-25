from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class Evidence:
    evidence_id:str; parents:tuple[str,...]; generation:int; source_digest:str
    def __post_init__(self):
        if not self.evidence_id or self.generation<0 or len(self.source_digest)!=64: raise Refused("REFUSED[INVALID_EVIDENCE]")
def admit_graph(nodes):
    rows=tuple(nodes); by={n.evidence_id:n for n in rows}
    if len(by)!=len(rows): raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
    for n in rows:
        if any(p not in by for p in n.parents): raise Refused("REFUSED[MISSING_EVIDENCE_PARENT]")
    visiting=set(); done=set()
    def visit(i):
        if i in visiting: raise Refused("REFUSED[CYCLIC_EVIDENCE_GRAPH]")
        if i in done:return
        visiting.add(i)
        for p in by[i].parents: visit(p)
        visiting.remove(i); done.add(i)
    for i in sorted(by): visit(i)
    return by
def ancestors(by,evidence_id):
    out=set()
    def walk(i):
        for p in by[i].parents:
            if p not in out: out.add(p); walk(p)
    walk(evidence_id); return frozenset(out)
