from dataclasses import dataclass
from itertools import combinations
from .refusal import Refused

@dataclass(frozen=True)
class CompatibilityHypergraph:
    forbidden: frozenset[frozenset[str]]
    def feasible(self, policies: tuple[str, ...]) -> bool:
        chosen = frozenset(policies)
        return not any(edge <= chosen for edge in self.forbidden)
    def maximal_feasible(self, policies: tuple[str, ...], max_size: int) -> tuple[tuple[str,...], ...]:
        if max_size < 1: raise Refused("INVALID_PORTFOLIO_SIZE")
        all_sets=[]
        for r in range(1, min(max_size, len(policies))+1):
            all_sets += [tuple(c) for c in combinations(sorted(policies), r) if self.feasible(tuple(c))]
        maximal=[]
        for c in all_sets:
            s=set(c)
            if not any(s < set(d) for d in all_sets): maximal.append(c)
        return tuple(sorted(maximal))
