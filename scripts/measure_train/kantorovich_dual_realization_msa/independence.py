from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class IndependenceWitness:
    left_impl:str; right_impl:str; left_model:str; right_model:str
    def admit(self):
        if self.left_impl==self.right_impl or self.left_model==self.right_model: raise Refused("REFUSED[UNPROVEN_ORACLE_INDEPENDENCE]")
        return True
