from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

class GraphRefusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Edge:
    upstream: str
    downstream: str

def dependency_closure(root: str, edges: Iterable[Edge]) -> tuple[str, ...]:
    deps: dict[str, set[str]] = {}
    for edge in edges:
        if edge.upstream == edge.downstream:
            raise GraphRefusal("REFUSED[SELF_DEPENDENCY]")
        deps.setdefault(edge.downstream, set()).add(edge.upstream)
        deps.setdefault(edge.upstream, set())
    if root not in deps:
        return (root,)
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []
    def visit(node: str) -> None:
        if node in visiting:
            raise GraphRefusal("REFUSED[DEPENDENCY_CYCLE]")
        if node in visited:
            return
        visiting.add(node)
        for dep in sorted(deps.get(node, ())):
            visit(dep)
        visiting.remove(node)
        visited.add(node)
        order.append(node)
    visit(root)
    return tuple(order)

def is_dependency_closed(root: str, selected: Iterable[str], edges: Iterable[Edge]) -> bool:
    return set(dependency_closure(root, edges)).issubset(set(selected))
