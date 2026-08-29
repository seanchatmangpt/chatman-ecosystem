from __future__ import annotations
from dataclasses import dataclass, field
from .subject import Subject

@dataclass
class DependencyGraph:
    edges: dict[Subject, set[Subject]] = field(default_factory=dict)

    def add(self, consumer: Subject, producer: Subject) -> None:
        if consumer == producer:
            raise ValueError('REFUSED[SELF_DEPENDENCY]')
        self.edges.setdefault(consumer, set()).add(producer)
        self.edges.setdefault(producer, set())
        self.order()

    def order(self) -> list[Subject]:
        visiting: set[Subject] = set(); done: set[Subject] = set(); out: list[Subject] = []
        def visit(node: Subject) -> None:
            if node in done: return
            if node in visiting: raise ValueError('REFUSED[DEPENDENCY_CYCLE]')
            visiting.add(node)
            for dep in sorted(self.edges.get(node, set())): visit(dep)
            visiting.remove(node); done.add(node); out.append(node)
        for node in sorted(self.edges): visit(node)
        return out

    def closure(self, root: Subject) -> set[Subject]:
        seen: set[Subject] = set()
        def walk(node: Subject) -> None:
            if node in seen: return
            seen.add(node)
            for dep in self.edges.get(node, set()): walk(dep)
        walk(root); return seen
