from dataclasses import dataclass
from .relation import Relation
from .refusal import Refused

@dataclass(frozen=True)
class MetamorphicWitness:
    relation: Relation
    stutter_idempotent: bool
    independent_commutation: bool

    def require(self) -> None:
        if self.relation in {Relation.STUTTER, Relation.EXACT} and not self.stutter_idempotent:
            raise Refused("REFUSED[STUTTER_LAW_FAILED]")
        if self.relation in {Relation.PARTIAL_ORDER, Relation.EXACT} and not self.independent_commutation:
            raise Refused("REFUSED[COMMUTATION_LAW_FAILED]")
