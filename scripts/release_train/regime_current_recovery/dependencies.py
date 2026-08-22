from dataclasses import dataclass
from .subject import Refusal, Subject

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[Subject,tuple[Subject,...]]
    def order(self, root: Subject) -> tuple[Subject,...]:
        state={}; ordered=[]
        def visit(node):
            mark=state.get(node,0)
            if mark==1: raise Refusal('REFUSED[DEPENDENCY_CYCLE]')
            if mark==2: return
            state[node]=1
            for dep in self.edges.get(node,()): visit(dep)
            state[node]=2; ordered.append(node)
        visit(root); return tuple(ordered)
    def blockers(self, root: Subject, standing: dict[Subject,str]) -> tuple[Subject,...]:
        return tuple(node for node in self.order(root) if standing.get(node,'UNKNOWN') in {'BLOCKED','BUILD_BROKEN'})
