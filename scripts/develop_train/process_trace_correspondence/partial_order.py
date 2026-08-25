from collections import Counter
from .trace import Trace
from .independence import Independence
def signature(t:Trace,ind:Independence):
    acts=[e.activity for e in t.events]; counts=tuple(sorted(Counter(acts).items())); deps=[]
    for i,a in enumerate(acts):
        for b in acts[i+1:]:
            if not ind.independent(a,b): deps.append((a,b))
    return counts,tuple(sorted(Counter(deps).items()))
def equivalent(a,b,ind): return signature(a,ind)==signature(b,ind)
