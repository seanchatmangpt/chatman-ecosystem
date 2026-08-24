from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class CausePartition:
    clusters:tuple
    @property
    def count(self): return len(self.clusters)
def partition(g,threshold=Fraction(1,2)):
    parent={x:x for x in g.ids}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    for e in g.edges:
        if e.common_cause or abs(e.rho)>=threshold: union(e.left,e.right)
    groups={}
    for x in g.ids: groups.setdefault(find(x),[]).append(x)
    return CausePartition(tuple(sorted(tuple(sorted(v)) for v in groups.values())))
