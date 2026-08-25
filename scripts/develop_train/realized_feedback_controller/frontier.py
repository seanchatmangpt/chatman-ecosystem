from dataclasses import dataclass
from .errors import Refused
from .policy import PolicyIdentity

@dataclass(frozen=True)
class PolicyFrontier:
    generation: int
    policies: tuple[PolicyIdentity, ...]

    @classmethod
    def current(cls, policies):
        if not policies:
            raise Refused("REFUSED_EMPTY_POLICY_FRONTIER")
        generation=max(p.generation for p in policies)
        current=tuple(p for p in policies if p.generation==generation)
        ids={p.policy_id for p in current}
        if len(ids)!=len(current):
            raise Refused("REFUSED_DIVERGENT_CURRENT_POLICY")
        return cls(generation, current)
