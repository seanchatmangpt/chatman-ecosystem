from dataclasses import dataclass
from .obligation import State
from .refusal import Refused

@dataclass(frozen=True)
class DependencyGraph:
    edges: dict[str, tuple[str,...]]

    def _visit(self,node,seen,stack):
        if node in stack: raise Refused("DEPENDENCY_CYCLE",node)
        if node in seen:return
        stack.add(node)
        for parent in self.edges.get(node,()): self._visit(parent,seen,stack)
        stack.remove(node);seen.add(node)

    def validate(self):
        seen=set()
        for n in self.edges:self._visit(n,seen,set())
        return self

    def blockers(self,node,states):
        self.validate(); out=set()
        for parent in self.edges.get(node,()):
            if states.get(parent) in {State.BLOCKED,State.BUILD_BROKEN}: out.add(parent)
            out.update(self.blockers(parent,states))
        return tuple(sorted(out))
