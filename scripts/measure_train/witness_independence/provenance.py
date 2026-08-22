from dataclasses import dataclass
from .subject import Refused

RELATIONS={"DERIVED_FROM","SHARES_RUN","SHARES_ARTIFACT","INDEPENDENT_ATTESTATION"}

@dataclass(frozen=True, order=True)
class ProvenanceEdge:
    left_id: str
    right_id: str
    relation: str
    def __post_init__(self):
        if not self.left_id or not self.right_id or self.left_id==self.right_id:
            raise Refused("REFUSED[INVALID_PROVENANCE_EDGE]")
        if self.relation not in RELATIONS:
            raise Refused("REFUSED[INVALID_PROVENANCE_RELATION]")

def validate_acyclic(observations, edges):
    ids={o.evidence_id for o in observations}
    parents={}
    for e in edges:
        if e.left_id not in ids or e.right_id not in ids:
            raise Refused("REFUSED[ORPHAN_PROVENANCE_EDGE]")
        if e.relation=="DERIVED_FROM":
            parents.setdefault(e.left_id,[]).append(e.right_id)
    visiting=set(); done=set()
    def visit(node):
        if node in visiting:
            raise Refused("REFUSED[PROVENANCE_CYCLE]")
        if node in done:
            return
        visiting.add(node)
        for parent in parents.get(node,()):
            visit(parent)
        visiting.remove(node); done.add(node)
    for node in ids:
        visit(node)
    return tuple(sorted(edges))
