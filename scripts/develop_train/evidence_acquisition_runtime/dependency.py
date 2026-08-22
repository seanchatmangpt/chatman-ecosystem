from dataclasses import dataclass
from .subject import Refusal
@dataclass(slots=True)
class DependencyGraph:
    edges:dict
    def __post_init__(self):
        visiting=set(); done=set()
        def visit(n):
            if n in visiting: raise Refusal('REFUSED_DEPENDENCY_CYCLE')
            if n in done: return
            visiting.add(n)
            for d in self.edges.get(n,set()): visit(d)
            visiting.remove(n); done.add(n)
        for n in self.edges: visit(n)
    def blockers(self,node,states):
        seen=set(); out=set()
        def walk(n):
            for d in self.edges.get(n,set()):
                if d in seen: continue
                seen.add(d)
                if states.get(d) in {'BUILD_BROKEN','BLOCKED'}: out.add(d)
                walk(d)
        walk(node); return tuple(sorted(out))
