from dataclasses import dataclass
from .epoch import ClosureEpoch
from .obligation import State
from .refusal import Refused

@dataclass(frozen=True)
class DependencyGraph:
    parents: dict[str, tuple[str, ...]]

    def __post_init__(self):
        graph={k:tuple(v) for k,v in self.parents.items()}
        seen,temp=set(),set()
        def visit(n):
            if n in temp: raise Refused("DEPENDENCY_CYCLE", n)
            if n in seen: return
            temp.add(n)
            for p in graph.get(n,()): visit(p)
            temp.remove(n); seen.add(n)
        for n in graph: visit(n)
        object.__setattr__(self,"parents",graph)

    def blocking_cut(self, epoch: ClosureEpoch) -> frozenset[str]:
        states={o.key:o.state for o in epoch.obligations}
        out=set()
        def red(k): return states.get(k, State.UNKNOWN) >= State.BLOCKED
        changed=True
        while changed:
            changed=False
            for child,parents in self.parents.items():
                if child in states and any(red(p) or p in out for p in parents):
                    for p in parents:
                        if red(p) and p not in out:
                            out.add(p); changed=True
        return frozenset(out)
