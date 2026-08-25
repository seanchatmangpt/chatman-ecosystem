from dataclasses import dataclass
from .errors import Refused
from .policy import FeedbackStrategy, PolicyIdentity

@dataclass(frozen=True)
class PolicyTransition:
    before: PolicyIdentity
    next_generation: int
    feedback: FeedbackStrategy

    def __post_init__(self):
        if self.next_generation != self.before.generation + 1:
            raise Refused("REFUSED_NON_MONOTONE_POLICY_GENERATION")
