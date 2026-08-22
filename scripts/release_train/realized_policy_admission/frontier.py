from dataclasses import dataclass
from .policy import Policy
import hashlib, json

@dataclass(frozen=True)
class PolicyFrontier:
    generation: int
    policy_digest: str
    realization_digest: str
    def __post_init__(self):
        if self.generation < 1 or any(len(x)!=64 for x in (self.policy_digest,self.realization_digest)):
            raise ValueError("REFUSED[INVALID_POLICY_FRONTIER]")
    @property
    def digest(self):
        return hashlib.sha256(json.dumps(self.__dict__,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def admit_frontier(frontier: PolicyFrontier, policy: Policy):
    if frontier.generation != policy.generation or frontier.policy_digest != policy.digest:
        raise ValueError("REFUSED[STALE_POLICY_FRONTIER]")
    return frontier
