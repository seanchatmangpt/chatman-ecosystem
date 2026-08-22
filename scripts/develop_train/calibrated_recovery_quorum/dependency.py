from __future__ import annotations

from dataclasses import dataclass

_RED = {"BUILD_BROKEN", "BLOCKED"}


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        graph: dict[str, list[str]] = {}
        for left, right in self.edges:
            graph.setdefault(left, []).append(right)
        visiting: set[str] = set()
        done: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if node in done:
                return
            visiting.add(node)
            for nxt in graph.get(node, []):
                visit(nxt)
            visiting.remove(node)
            done.add(node)

        for node in tuple(graph):
            visit(node)

    def blockers(self, root: str, standings: dict[str, str]) -> tuple[str, ...]:
        graph: dict[str, list[str]] = {}
        for left, right in self.edges:
            graph.setdefault(left, []).append(right)
        seen: set[str] = set()
        stack = list(graph.get(root, []))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(graph.get(node, []))
        return tuple(sorted(node for node in seen if standings.get(node) in _RED))
