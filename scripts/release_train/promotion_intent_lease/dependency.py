from dataclasses import dataclass
from .subject import Subject, Refusal

@dataclass(frozen=True)
class DependencyGraph:
    edges: tuple[tuple[Subject, Subject], ...]

    def closure(self, root: Subject) -> tuple[Subject, ...]:
        adj={}
        for src,dst in self.edges:
            adj.setdefault(src,[]).append(dst)
        seen=set(); stack=[]; out=[]
        def visit(node):
            if node in stack:
                raise Refusal('REFUSED[DEPENDENCY_CYCLE]')
            if node in seen: return
            stack.append(node)
            for dep in sorted(adj.get(node,[])):
                visit(dep)
            stack.pop(); seen.add(node); out.append(node)
        visit(root)
        return tuple(out)
