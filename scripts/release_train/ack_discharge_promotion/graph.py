from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class GraphRefusal(ValueError):
    pass

@dataclass(frozen=True)
class DependencyGraph:
    edges: tuple[tuple[Subject, Subject], ...]

    def __post_init__(self) -> None:
        nodes = {n for edge in self.edges for n in edge}
        if any(a == b for a, b in self.edges):
            raise GraphRefusal("REFUSED[SELF_DEPENDENCY]")
        indegree = {n: 0 for n in nodes}
        children = {n: [] for n in nodes}
        for parent, child in self.edges:
            indegree[child] += 1
            children[parent].append(child)
        ready = sorted([n for n, degree in indegree.items() if degree == 0])
        visited = 0
        while ready:
            node = ready.pop(0)
            visited += 1
            for child in sorted(children[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        if visited != len(nodes):
            raise GraphRefusal("REFUSED[DEPENDENCY_CYCLE]")

    def affected(self, producer: Subject) -> tuple[tuple[Subject, int], ...]:
        children: dict[Subject, list[Subject]] = {}
        for parent, child in self.edges:
            children.setdefault(parent, []).append(child)
        seen: dict[Subject, int] = {}
        frontier=[(producer,0)]
        while frontier:
            node, depth = frontier.pop(0)
            for child in sorted(children.get(node, [])):
                next_depth=depth+1
                if child not in seen or next_depth < seen[child]:
                    seen[child]=next_depth
                    frontier.append((child,next_depth))
        return tuple(sorted(seen.items(), key=lambda item:(item[1], item[0])))
