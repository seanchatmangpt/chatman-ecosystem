from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
ACTIONS={"INDEPENDENT","DEPENDENT","DEFER"}
@dataclass(frozen=True, order=True)
class DecisionPolicy:
    policy_id:str; generation:int; digest:str
    false_independent_loss:Fraction; false_dependent_loss:Fraction; defer_loss:Fraction
    def __post_init__(self):
        if not self.policy_id or self.generation<0: raise Refused("REFUSED[INVALID_POLICY_IDENTITY]")
        if len(self.digest)!=64: raise Refused("REFUSED[INVALID_POLICY_DIGEST]")
        if any(x<0 for x in (self.false_independent_loss,self.false_dependent_loss,self.defer_loss)): raise Refused("REFUSED[NEGATIVE_LOSS]")
    def realized_loss(self,decision,truth):
        if decision not in ACTIONS: raise Refused("REFUSED[UNKNOWN_DECISION]")
        if truth not in {"INDEPENDENT","DEPENDENT"}: raise Refused("REFUSED[UNKNOWN_TRUTH]")
        if decision=="DEFER": return self.defer_loss
        if decision==truth: return Fraction(0)
        return self.false_independent_loss if decision=="INDEPENDENT" else self.false_dependent_loss
