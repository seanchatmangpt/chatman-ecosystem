from __future__ import annotations
from dataclasses import dataclass
from .identity import Subject
@dataclass(frozen=True,slots=True)
class DependencyGraph:
    edges:tuple[tuple[Subject,Subject],...]
    def __post_init__(self)->None:
        nodes={n for e in self.edges for n in e}; graph={n:[] for n in nodes}
        for a,b in self.edges:
            if a==b: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            graph[a].append(b)
        visiting=set(); done=set()
        def dfs(n):
            if n in visiting: raise ValueError("REFUSED[DEPENDENCY_CYCLE]")
            if n in done: return
            visiting.add(n)
            for m in graph[n]: dfs(m)
            visiting.remove(n); done.add(n)
        for n in nodes: dfs(n)
    def blocked(self,standing:dict[Subject,str])->set[Subject]:
        blocked={s for s,state in standing.items() if state in {"BUILD_BROKEN","BLOCKED"}}
        changed=True
        while changed:
            changed=False
            for p,c in self.edges:
                if p in blocked and c not in blocked: blocked.add(c); changed=True
        return blocked
