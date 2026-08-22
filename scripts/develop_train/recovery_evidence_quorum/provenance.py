from __future__ import annotations

from dataclasses import dataclass, field

from .subject import Refused


@dataclass(slots=True)
class ProvenanceGraph:
    parents: dict[str, set[str]] = field(default_factory=dict)

    def add(self, child: str, parent: str) -> None:
        if not child or not parent or child == parent:
            raise Refused("REFUSED[INVALID_PROVENANCE_EDGE]")
        self.parents.setdefault(child, set()).add(parent)
        self.parents.setdefault(parent, set())
        if self._has_cycle():
            self.parents[child].remove(parent)
            raise Refused("REFUSED[PROVENANCE_CYCLE]")

    def derives_from(self, child: str, ancestor: str) -> bool:
        seen: set[str] = set()
        stack = list(self.parents.get(child, ()))
        while stack:
            node = stack.pop()
            if node == ancestor:
                return True
            if node not in seen:
                seen.add(node)
                stack.extend(self.parents.get(node, ()))
        return False

    def _has_cycle(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for parent in self.parents.get(node, ()):
                if visit(parent):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in tuple(self.parents))
