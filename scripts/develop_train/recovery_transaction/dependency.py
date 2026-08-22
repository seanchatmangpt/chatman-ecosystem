from __future__ import annotations
from dataclasses import dataclass
from .subject import Refusal

_BAD = {"BUILD_BROKEN", "BLOCKED"}

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[str, tuple[str, ...]]
    def __post_init__(self) -> None:
        nodes = set(self.edges)
        for deps in self.edges.values():
            nodes.update(deps)
        for node in nodes:
            self._visit(node, set(), set())
    def _visit(self, node: str, visiting: set[str], visited: set[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            raise Refusal("DEPENDENCY_CYCLE", node)
        visiting.add(node)
        for dep in self.edges.get(node, ()):
            self._visit(dep, visiting, visited)
        visiting.remove(node)
        visited.add(node)
    def blockers(self, node: str, standings: dict[str, str]) -> tuple[str, ...]:
        out = set()
        stack = list(self.edges.get(node, ()))
        while stack:
            dep = stack.pop()
            if standings.get(dep, "UNKNOWN") in _BAD:
                out.add(dep)
            stack.extend(self.edges.get(dep, ()))
        return tuple(sorted(out))
