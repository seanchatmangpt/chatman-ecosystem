from dataclasses import dataclass
from .errors import Refused
from .subject import Subject

_RED={"BLOCKED","BUILD_BROKEN"}

@dataclass
class DependencyGraph:
    edges: dict
    standing: dict
    def __init__(self): self.edges={}; self.standing={}
    def add(self,subject:Subject,dependencies=(),standing="UNKNOWN"):
        self.edges[subject]=tuple(dependencies); self.standing[subject]=standing
    def _visit(self,node,stack,seen):
        if node in stack: raise Refused("DEPENDENCY_CYCLE")
        if node in seen: return
        stack.add(node)
        for dep in self.edges.get(node,()):
            if dep not in self.edges: raise Refused("UNKNOWN_DEPENDENCY")
            self._visit(dep,stack,seen)
        stack.remove(node); seen.add(node)
    def blockers(self,root):
        self._visit(root,set(),set()); reachable=set()
        def walk(node):
            for dep in self.edges.get(node,()):
                if dep not in reachable: reachable.add(dep); walk(dep)
        walk(root)
        return tuple(sorted(d.canonical() for d in reachable if self.standing.get(d) in _RED))
