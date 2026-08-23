from dataclasses import dataclass
from .refusal import Refused
_BAD={"BUILD_BROKEN","BLOCKED"}
@dataclass(frozen=True)
class DependencyGraph:
    edges:tuple[tuple[str,str],...]; standing:tuple[tuple[str,str],...]
    def ordered(self)->tuple[str,...]:
        nodes=set(dict(self.standing)); [nodes.update(x) for x in self.edges]
        incoming={n:0 for n in nodes}; children={n:[] for n in nodes}
        for parent,child in self.edges: incoming[child]+=1; children[parent].append(child)
        ready=sorted(n for n,v in incoming.items() if v==0); out=[]
        while ready:
            n=ready.pop(0); out.append(n)
            for c in sorted(children[n]):
                incoming[c]-=1
                if incoming[c]==0: ready.append(c); ready.sort()
        if len(out)!=len(nodes): raise Refused("DEPENDENCY_CYCLE")
        return tuple(out)
    def blockers(self)->tuple[str,...]:
        self.ordered(); return tuple(sorted(k for k,v in self.standing if v in _BAD))
