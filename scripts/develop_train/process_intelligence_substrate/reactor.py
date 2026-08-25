from __future__ import annotations
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class ReactorStep:
    name: str
    requires: tuple[str, ...] = ()


def topological_order(steps: tuple[ReactorStep, ...]) -> tuple[str, ...]:
    graph = {s.name: set(s.requires) for s in steps}
    if len(graph) != len(steps):
        raise Refused("DUPLICATE_REACTOR_STEP")
    unknown = {d for deps in graph.values() for d in deps if d not in graph}
    if unknown:
        raise Refused("FOREIGN_REACTOR_DEPENDENCY", ",".join(sorted(unknown)))
    out: list[str] = []
    while graph:
        ready = sorted(k for k, deps in graph.items() if not deps)
        if not ready:
            raise Refused("REACTOR_CYCLE")
        for name in ready:
            out.append(name); graph.pop(name)
            for deps in graph.values(): deps.discard(name)
    return tuple(out)
