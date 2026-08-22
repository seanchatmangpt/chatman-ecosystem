from __future__ import annotations

from dataclasses import dataclass

from .model import ExactSubject, Refused


@dataclass(frozen=True)
class DependencyEdge:
    upstream: ExactSubject
    downstream: ExactSubject


def dependency_order(subjects: list[ExactSubject], edges: list[DependencyEdge]) -> list[ExactSubject]:
    nodes = {subject.coordinate: subject for subject in subjects}
    if len(nodes) != len(subjects):
        raise Refused("DUPLICATE_DEPENDENCY_SUBJECT")
    outgoing: dict[str, set[str]] = {key: set() for key in nodes}
    indegree = {key: 0 for key in nodes}
    for edge in edges:
        a, b = edge.upstream.coordinate, edge.downstream.coordinate
        if a not in nodes or b not in nodes:
            raise Refused("DEPENDENCY_EDGE_OUTSIDE_CLOSURE")
        if a == b:
            raise Refused("DEPENDENCY_SELF_EDGE", a)
        if b not in outgoing[a]:
            outgoing[a].add(b)
            indegree[b] += 1
    ready = sorted(key for key, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for nxt in sorted(outgoing[current]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    if len(order) != len(nodes):
        raise Refused("DEPENDENCY_CYCLE")
    return [nodes[key] for key in order]
