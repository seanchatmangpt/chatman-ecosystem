from dataclasses import dataclass
from enum import Enum
from .domain import nonnegative
from .errors import Refused
class Decision(str, Enum):
    INDEPENDENT="INDEPENDENT"; DEPENDENT="DEPENDENT"; DEFER="DEFER"
@dataclass(frozen=True)
class LossMatrix:
    false_independent: object; false_dependent: object; defer: object
    def __post_init__(self):
        object.__setattr__(self,"false_independent",nonnegative(self.false_independent)); object.__setattr__(self,"false_dependent",nonnegative(self.false_dependent)); object.__setattr__(self,"defer",nonnegative(self.defer))
        if self.false_independent == self.false_dependent: raise Refused("LOSS_COLLAPSE")
@dataclass(frozen=True)
class DecisionPolicy:
    policy_id:str; generation:int; digest:str; loss:LossMatrix
    def __post_init__(self):
        if not self.policy_id or self.generation < 1: raise Refused("INVALID_POLICY")
        if len(self.digest)!=64 or any(c not in "0123456789abcdef" for c in self.digest): raise Refused("INVALID_POLICY_DIGEST")
