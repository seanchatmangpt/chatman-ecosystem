from dataclasses import dataclass
from .identity import PolicyIdentity
from .refusal import Refused
@dataclass(frozen=True)
class CompatibilityHypergraph:
    forbidden:frozenset[frozenset[str]]
    def feasible(self, policies:tuple[PolicyIdentity,...])->bool:
        ds=frozenset(p.digest for p in policies)
        return not any(edge<=ds for edge in self.forbidden)
    def maximal_feasible(self, policies:tuple[PolicyIdentity,...], max_size:int)->tuple[tuple[PolicyIdentity,...],...]:
        if max_size<1: raise Refused('INVALID_PORTFOLIO_SIZE')
        from itertools import combinations
        candidates=[]
        for r in range(1,min(max_size,len(policies))+1):
            candidates += [c for c in combinations(sorted(policies),r) if self.feasible(c)]
        return tuple(c for c in candidates if not any(set(c)<set(d) for d in candidates))
