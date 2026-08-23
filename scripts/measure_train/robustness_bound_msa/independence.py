from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class IndependenceProof:
    left: str
    right: str
    distinct_implementation: bool
    distinct_model: bool
    def admit(self):
        if self.left==self.right: raise Refused("REFUSED[SELF_INDEPENDENCE]")
        if not self.distinct_implementation or not self.distinct_model:
            raise Refused("REFUSED[UNPROVEN_BOUND_INDEPENDENCE]")
        return True
