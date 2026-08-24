from dataclasses import dataclass
from .observation import Relation
from .errors import Refused
@dataclass(frozen=True)
class Lineage: exact:int; advanced:int; diverged:int; censored:int
def classify(observations): return Lineage(sum(o.relation==Relation.EXACT for o in observations),sum(o.relation==Relation.ADVANCED for o in observations),sum(o.relation==Relation.DIVERGED for o in observations),sum(o.relation==Relation.CENSORED for o in observations))
def require_no_divergence(l):
    if l.diverged: raise Refused("SEMANTIC_LINEAGE_DIVERGENCE")
    return l
