from dataclasses import dataclass

RED={"BLOCKED","BUILD_BROKEN"}

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict
    standings: dict
    def __post_init__(self):
        nodes=set(self.edges)|{d for ds in self.edges.values() for d in ds}
        visiting=set(); done=set()
        def visit(n):
            if n in visiting: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if n in done: return
            visiting.add(n)
            for d in self.edges.get(n,()): visit(d)
            visiting.remove(n); done.add(n)
        for n in nodes: visit(n)
    def blockers(self, node):
        found=set()
        def walk(n):
            for d in self.edges.get(n,()):
                if self.standings.get(d) in RED: found.add(d)
                walk(d)
        walk(node)
        return tuple(sorted(found))
