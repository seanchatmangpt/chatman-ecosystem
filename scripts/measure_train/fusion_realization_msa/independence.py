from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class IndependenceProof:
    left: str
    right: str
    frontier_digest: str
    observed_overlap: float
    def __post_init__(self):
        if self.left==self.right: raise Refused("REFUSED[SELF_INDEPENDENCE]")
        if len(self.frontier_digest)!=64 or not (0<=self.observed_overlap<=1): raise Refused("REFUSED[INVALID_INDEPENDENCE_PROOF]")
def admit_independence(a,b,proof,max_overlap=0.5):
    if {proof.left,proof.right}!={a.sensor_id,b.sensor_id}: raise Refused("REFUSED[FOREIGN_INDEPENDENCE_PROOF]")
    if a.family==b.family or a.runtime==b.runtime or a.artifact_digest==b.artifact_digest: raise Refused("REFUSED[STRUCTURALLY_CORRELATED_SENSORS]")
    if proof.observed_overlap>max_overlap: raise Refused("REFUSED[EMPIRICALLY_OVERLAPPING_SENSORS]")
    return "INDEPENDENT"
