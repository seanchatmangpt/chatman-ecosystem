from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class PowlModel:
    activities: tuple[str,...]
    order_edges: tuple[tuple[str,str],...]
    choice_edges: tuple[tuple[str,str],...]=()
    cycle_bound: int=0
    def __post_init__(self):
        nodes=set(self.activities)
        if len(nodes)!=len(self.activities) or any(a=="" for a in nodes): raise Refused("REFUSED[INVALID_POWL_ACTIVITY]")
        if any(a not in nodes or b not in nodes or a==b for a,b in self.order_edges): raise Refused("REFUSED[INVALID_POWL_ORDER_EDGE]")
        graph={n:[] for n in nodes}
        for a,b in self.order_edges: graph[a].append(b)
        visiting=set(); done=set()
        def visit(n):
            if n in visiting: raise Refused("REFUSED[CYCLIC_STRICT_PARTIAL_ORDER]")
            if n in done: return
            visiting.add(n)
            for m in graph[n]: visit(m)
            visiting.remove(n); done.add(n)
        for n in nodes: visit(n)
        if self.choice_edges and self.cycle_bound<=0: raise Refused("REFUSED[UNBOUNDED_CHOICE_CYCLE]")
    def dependencies(self): return tuple(sorted(set(self.order_edges)))
