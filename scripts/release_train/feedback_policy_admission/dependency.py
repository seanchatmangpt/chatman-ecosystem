from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class DependencyGraph:
    edges: dict
    states: dict
    def blockers(self, node):
        seen=set(); stack=[node]; blockers=set()
        while stack:
            cur=stack.pop()
            if cur in seen: continue
            seen.add(cur)
            for dep in self.edges.get(cur,()):
                if dep==node: raise Refused("DEPENDENCY_CYCLE")
                state=self.states.get(dep,"UNKNOWN")
                if state in {"BUILD_BROKEN","BLOCKED"}: blockers.add(dep)
                if dep in seen and dep!=cur: continue
                stack.append(dep)
        return tuple(sorted(blockers))
