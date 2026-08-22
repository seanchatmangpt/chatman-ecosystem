from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject, Refusal
_BLOCKING={"BUILD_BROKEN","BLOCKED"}
@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[str, tuple[str,...]]
    def order(self, root: str) -> tuple[str,...]:
        out=[]; temp=set(); done=set()
        def visit(n:str)->None:
            if n in temp: raise Refusal("REFUSED[DEPENDENCY_CYCLE]")
            if n in done:return
            temp.add(n)
            for d in sorted(self.edges.get(n,())): visit(d)
            temp.remove(n); done.add(n); out.append(n)
        visit(root); return tuple(out)
    def blockers(self, root: str, standing: dict[str,str]) -> tuple[str,...]:
        return tuple(n for n in self.order(root) if standing.get(n,"UNKNOWN") in _BLOCKING)
