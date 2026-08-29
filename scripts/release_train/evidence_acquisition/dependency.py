from dataclasses import dataclass

@dataclass(frozen=True)
class DependencyGraph:
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self):
        nodes = {node for edge in self.edges for node in edge}
        graph = {node: set() for node in nodes}
        for parent, child in self.edges:
            if parent == child:
                raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            graph[parent].add(child)
        visiting: set[str] = set()
        visited: set[str] = set()
        def walk(node: str) -> None:
            if node in visiting:
                raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if node in visited:
                return
            visiting.add(node)
            for child in graph[node]:
                walk(child)
            visiting.remove(node)
            visited.add(node)
        for node in sorted(nodes):
            walk(node)

    def blockers(self, root: str, standing: dict[str, str]) -> tuple[str, ...]:
        graph: dict[str, set[str]] = {}
        for parent, child in self.edges:
            graph.setdefault(parent, set()).add(child)
        blocked: set[str] = set()
        seen: set[str] = set()
        def visit(node: str) -> None:
            if node in seen:
                return
            seen.add(node)
            for child in graph.get(node, set()):
                if standing.get(child) in {"BUILD_BROKEN", "BLOCKED"}:
                    blocked.add(child)
                visit(child)
        visit(root)
        return tuple(sorted(blocked))
