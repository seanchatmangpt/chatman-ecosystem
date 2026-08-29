from dataclasses import dataclass
from .refusal import Refused
RED={"BUILD_BROKEN","BLOCKED"}
@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[str, tuple[str,...]]
    states: dict[str,str]
    def blockers(self, root: str) -> tuple[str,...]:
        seen=set(); active=set(); blocked=set()
        def walk(n):
            if n in active: raise Refused("DEPENDENCY_CYCLE")
            if n in seen: return
            active.add(n)
            if self.states.get(n) in RED: blocked.add(n)
            for d in self.edges.get(n,()): walk(d)
            active.remove(n); seen.add(n)
        walk(root)
        return tuple(sorted(blocked))
