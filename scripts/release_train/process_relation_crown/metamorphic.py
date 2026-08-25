from dataclasses import dataclass
from .relation import Relation
from .refusal import Refused
@dataclass(frozen=True)
class MetamorphicWitness:
    relation:Relation; laws:frozenset[str]
    def require(self):
        required={"reflexive","deterministic"}
        if self.relation==Relation.STUTTER: required|={"stutter_invariant"}
        if self.relation==Relation.PARTIAL_ORDER: required|={"independent_commutation"}
        if not required<=self.laws: raise Refused("METAMORPHIC_LAW_GAP")
        return True
