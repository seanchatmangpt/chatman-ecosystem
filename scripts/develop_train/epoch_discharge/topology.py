from __future__ import annotations
from dataclasses import dataclass
from .identity import Subject

@dataclass(frozen=True, slots=True)
class DependencyGraph:
    edges: dict[Subject, tuple[Subject,...]]
    def __post_init__(self)->None:
        nodes=set(self.edges)
        for children in self.edges.values(): nodes.update(children)
        visiting:set[Subject]=set(); done:set[Subject]=set()
        def walk(node:Subject)->None:
            if node in visiting: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if node in done: return
            visiting.add(node)
            for child in self.edges.get(node, ()): walk(child)
            visiting.remove(node); done.add(node)
        for node in sorted(nodes, key=lambda x:x.value): walk(node)
    def affected(self, producer:Subject)->tuple[tuple[Subject,int],...]:
        out:dict[Subject,int]={}; queue=[(producer,0)]
        while queue:
            node,depth=queue.pop(0)
            for child in self.edges.get(node,()):
                nd=depth+1
                if child not in out or nd<out[child]: out[child]=nd; queue.append((child,nd))
        return tuple(sorted(out.items(), key=lambda x:(x[1],x[0].value)))
