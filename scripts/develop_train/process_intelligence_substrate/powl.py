from __future__ import annotations
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class PowlNode:
    name: str
    successors: tuple[str, ...] = ()

@dataclass(frozen=True)
class PowlModel:
    start: str
    nodes: tuple[PowlNode, ...]
    step_bound: int

    def __post_init__(self) -> None:
        if self.step_bound <= 0:
            raise Refused("POWL_UNBOUNDED")
        names = {n.name for n in self.nodes}
        if self.start not in names:
            raise Refused("POWL_START")
        if any(s not in names for n in self.nodes for s in n.successors):
            raise Refused("POWL_FOREIGN_EDGE")

    def reachable(self) -> frozenset[str]:
        graph = {n.name: n.successors for n in self.nodes}
        seen: set[str] = set()
        frontier = [self.start]
        steps = 0
        while frontier and steps < self.step_bound:
            current = frontier.pop(0)
            if current in seen:
                steps += 1; continue
            seen.add(current)
            frontier.extend(graph[current])
            steps += 1
        return frozenset(seen)
