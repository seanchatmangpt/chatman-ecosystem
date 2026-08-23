from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class PolicyFrontier:
    policies: tuple
    def current(self):
        if not self.policies: raise Refused("EMPTY_POLICY_FRONTIER")
        g=max(p.generation for p in self.policies)
        latest=tuple(p for p in self.policies if p.generation==g)
        sig={(p.digest,p.strategy.value) for p in latest}
        if len(sig)!=1: raise Refused("DIVERGENT_POLICY_FRONTIER")
        return latest[0]
    def require(self, expected):
        cur=self.current()
        if cur != expected: raise Refused("STALE_POLICY")
        return cur
