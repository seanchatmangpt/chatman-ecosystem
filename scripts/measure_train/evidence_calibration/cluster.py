from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class EvidenceCluster:
    cluster_id:str
    source_ids:tuple[str,...]
    def __post_init__(self):
        if not self.cluster_id or not self.source_ids: raise Refused("REFUSED[EMPTY_CLUSTER]")
        if len(self.source_ids)!=len(set(self.source_ids)): raise Refused("REFUSED[DUPLICATE_CLUSTER_SOURCE]")
def validate_disjoint(clusters):
    seen=set()
    for c in clusters:
        overlap=seen.intersection(c.source_ids)
        if overlap: raise Refused("REFUSED[NONINDEPENDENT_CALIBRATION_CLUSTERS]")
        seen.update(c.source_ids)
    return tuple(sorted(clusters))
