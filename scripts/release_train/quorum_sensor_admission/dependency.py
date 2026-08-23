from __future__ import annotations

from dataclasses import dataclass

from .errors import Refused
from .subject import Subject

_BAD = {"BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}


@dataclass(frozen=True)
class DependencyNode:
    subject: Subject
    standing: str


@dataclass
class DependencyGraph:
    edges: dict[Subject, tuple[Subject, ...]]
    standings: dict[Subject, str]

    def _visit(self, node: Subject, visiting: set[Subject], seen: set[Subject]) -> None:
        if node in visiting:
            raise Refused("DEPENDENCY_CYCLE", node.canonical())
        if node in seen:
            return
        visiting.add(node)
        for dep in self.edges.get(node, ()):
            self._visit(dep, visiting, seen)
        visiting.remove(node)
        seen.add(node)

    def validate(self, root: Subject) -> None:
        self._visit(root, set(), set())

    def blockers(self, root: Subject) -> tuple[str, ...]:
        self.validate(root)
        out: set[str] = set()
        stack = list(self.edges.get(root, ()))
        seen: set[Subject] = set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            standing = self.standings.get(node, "UNKNOWN")
            if standing in _BAD:
                out.add(f"{node.canonical()}:{standing}")
            stack.extend(self.edges.get(node, ()))
        return tuple(sorted(out))
