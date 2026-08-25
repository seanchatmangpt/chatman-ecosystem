from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class LossMatrix:
    false_independent: Fraction
    false_dependent: Fraction
    defer: Fraction
    def __post_init__(self):
        if min(self.false_independent, self.false_dependent, self.defer) < 0:
            raise Refused("NEGATIVE_LOSS")

@dataclass(frozen=True)
class DecisionPolicy:
    policy_id: str
    generation: int
    digest: str
    losses: LossMatrix
    def __post_init__(self):
        if not self.policy_id or self.generation < 0 or len(self.digest) != 64:
            raise Refused("INVALID_POLICY_IDENTITY")
