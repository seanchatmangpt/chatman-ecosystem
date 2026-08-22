from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class ProvenanceEdge:
    child_id: str
    parent_id: str
    relation: str
    def __post_init__(self):
        if not self.child_id or not self.parent_id or self.child_id==self.parent_id:
            raise Refused("REFUSED[INVALID_PROVENANCE_EDGE]")
        if self.relation not in {"DERIVED_FROM","EXECUTED_BY","PRODUCED","ATTESTS"}:
            raise Refused("REFUSED[INVALID_PROVENANCE_RELATION]")
