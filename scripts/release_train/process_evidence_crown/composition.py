from dataclasses import dataclass
from .evidence import EvidenceNode,Outcome
from .interval import Interval
from .provenance import ProvenanceWitness, require_distinct
from .refusal import Refused

@dataclass(frozen=True)
class Composition:
    ids:tuple[str,...]; interval:Interval; independent:bool

def compose(nodes:list[EvidenceNode], witnesses:list[ProvenanceWitness]=()):
    if not nodes: raise Refused("EMPTY_EVIDENCE_COMPOSITION")
    if any(n.outcome==Outcome.FAIL for n in nodes): raise Refused("FAILED_EVIDENCE_IN_COMPOSITION")
    cur=nodes[0].confidence; independent=True
    wmap={frozenset((w.left,w.right)):w for w in witnesses}
    for i,n in enumerate(nodes[1:],1):
        ok=True
        for prev in nodes[:i]:
            w=wmap.get(frozenset((prev.id,n.id)))
            if w is None: ok=False; break
            require_distinct(prev,n,w)
        if ok: cur=cur.independent_and(n.confidence)
        else: cur=cur.conservative_and(n.confidence); independent=False
    return Composition(tuple(sorted(n.id for n in nodes)),cur,independent)
