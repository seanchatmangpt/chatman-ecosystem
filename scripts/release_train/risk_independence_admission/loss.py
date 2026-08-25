from dataclasses import dataclass
from .probability import nonnegative

@dataclass(frozen=True)
class LossMatrix:
    false_independent: object
    false_dependent: object
    defer: object
    def __post_init__(self):
        object.__setattr__(self,'false_independent',nonnegative(self.false_independent))
        object.__setattr__(self,'false_dependent',nonnegative(self.false_dependent))
        object.__setattr__(self,'defer',nonnegative(self.defer))
