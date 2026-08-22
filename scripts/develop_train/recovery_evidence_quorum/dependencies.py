from __future__ import annotations

from dataclasses import dataclass, field

from .policy import Standing
from .subject import Refused


@dataclass(slots=True)
class DependencyGraph:
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add(self, node: str, depends_on: str) -> None:
        self.edges.setdefault(node, set()).add(depends_on)
        self.edges.setdefault(depends_on, set())
        if self._cycle():
            self.edges[node].remove(depends_on)
            raise Refused("REFUSED[DEPENDENCY_CYCLE]")

    def blockers(self, root: str, standings: dict[str, Standing]) -> tuple[str, ...]:
        seen: set[str] = set()
        stack = list(self.edges.get(root, ()))
        blockers: set[str] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            standing = standings.get(node, Standing.UNKNOWN)
            if standing in {Standing.BUILD_BROKEN, Standing.BLOCKED}:
                blockers.add(node)
            stack.extend(self.edges.get(node, ()))
        return tuple(sorted(blockers))

    def _cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            if any(visit(dep) for dep in self.edges.get(node, ())):
                return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in tuple(self.edges))
