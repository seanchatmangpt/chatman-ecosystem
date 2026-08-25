from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class IndependenceWitness:
    left:str; right:str; implementation_distinct:bool; model_distinct:bool; evidence_root_distinct:bool
    def admit(self):
        if self.left==self.right: raise Refused("REFUSED[SELF_INDEPENDENCE]")
        if not (self.implementation_distinct and self.model_distinct and self.evidence_root_distinct): raise Refused("REFUSED[UNPROVEN_ORACLE_INDEPENDENCE]")
        return True
