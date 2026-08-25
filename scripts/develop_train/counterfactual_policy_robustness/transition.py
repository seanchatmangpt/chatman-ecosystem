from dataclasses import dataclass
from .policy import PolicyIdentity
from .strategies import RobustStrategy
from .errors import Refused
@dataclass(frozen=True, slots=True)
class PolicyTransition:
    before:PolicyIdentity; after:PolicyIdentity; strategy:RobustStrategy
    def __post_init__(self):
        if self.after.generation != self.before.generation + 1: raise Refused('REFUSED_NON_MONOTONE_POLICY_GENERATION')
        if self.before.digest == self.after.digest: raise Refused('REFUSED_NOOP_POLICY_TRANSITION')
