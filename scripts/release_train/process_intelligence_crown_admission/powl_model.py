from dataclasses import dataclass
from .refusal import require

@dataclass(frozen=True)
class PowlModel:
    activities: tuple[str, ...]
    strict_order: frozenset[tuple[str, str]]
    choice_edges: frozenset[tuple[str, str]]
    start: str
    terminal: str
    bound: int

    def __post_init__(self):
        nodes=set(self.activities)
        require(len(nodes)==len(self.activities) and nodes, "INVALID_POWL_ACTIVITIES")
        require(self.start in nodes and self.terminal in nodes, "INVALID_POWL_TERMINALS")
        require(self.bound > 0, "UNBOUNDED_POWL")
        for a,b in self.strict_order | self.choice_edges:
            require(a in nodes and b in nodes and a != b, "FOREIGN_POWL_EDGE")
        graph={n:set() for n in nodes}
        for a,b in self.strict_order: graph[a].add(b)
        visiting=set(); done=set()
        def visit(n):
            if n in visiting: return False
            if n in done: return True
            visiting.add(n)
            if any(not visit(m) for m in graph[n]): return False
            visiting.remove(n); done.add(n); return True
        require(all(visit(n) for n in nodes), "CYCLIC_STRICT_ORDER")
