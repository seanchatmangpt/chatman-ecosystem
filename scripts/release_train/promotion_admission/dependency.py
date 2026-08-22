from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class DependencyRefusal(ValueError):
    pass

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[Subject, frozenset[Subject]]

    def closure(self, roots: frozenset[Subject]) -> tuple[Subject, ...]:
        seen: set[Subject] = set()
        active: set[Subject] = set()
        ordered: list[Subject] = []
        def visit(node: Subject) -> None:
            if node in active:
                raise DependencyRefusal("REFUSED[DEPENDENCY_CYCLE]")
            if node in seen:
                return
            active.add(node)
            for dep in sorted(self.edges.get(node, frozenset()), key=lambda s: s.identity):
                visit(dep)
            active.remove(node); seen.add(node); ordered.append(node)
        for root in sorted(roots, key=lambda s: s.identity):
            visit(root)
        return tuple(ordered)

    def assert_closed(self, selected: frozenset[Subject]) -> None:
        for node in selected:
            missing = self.edges.get(node, frozenset()) - selected
            if missing:
                raise DependencyRefusal("REFUSED[INCOMPLETE_DEPENDENCY_CLOSURE]")
