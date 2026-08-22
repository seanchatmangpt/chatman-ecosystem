from __future__ import annotations
from dataclasses import dataclass
from .identity import Refusal
@dataclass(frozen=True, slots=True)
class DependencyGraph:
    edges: dict[str, tuple[str, ...]]
    def __post_init__(self) -> None:
        visiting: set[str] = set(); visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise Refusal("REFUSED[DEPENDENCY_CYCLE]")
            if node in visited: return
            visiting.add(node)
            for dep in self.edges.get(node, ()): visit(dep)
            visiting.remove(node); visited.add(node)
        for node in sorted(set(self.edges) | {d for deps in self.edges.values() for d in deps}): visit(node)
    def closure(self, root: str) -> tuple[str, ...]:
        seen: set[str] = set()
        def walk(node: str) -> None:
            if node in seen: return
            seen.add(node)
            for dep in self.edges.get(node, ()): walk(dep)
        walk(root)
        return tuple(sorted(seen))
