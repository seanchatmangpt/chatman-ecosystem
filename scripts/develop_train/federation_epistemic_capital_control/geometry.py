from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class CorrelationEdge:
    left:str; right:str; rho:Fraction; mutual_information:Fraction=Fraction(0); common_cause:bool=False
    def __post_init__(self):
        if self.left==self.right: raise Refused("SELF_CORRELATION_EDGE")
        if not Fraction(-1)<=self.rho<=Fraction(1): raise Refused("INVALID_CORRELATION")
        if self.mutual_information<0: raise Refused("NEGATIVE_MUTUAL_INFORMATION")
class CorrelationGeometry:
    def __init__(self,ids,edges=()):
        self.ids=tuple(sorted(set(ids))); self.index={x:i for i,x in enumerate(self.ids)}
        if not self.ids: raise Refused("EMPTY_CORRELATION_GEOMETRY")
        n=len(self.ids); self.matrix=[[Fraction(int(i==j)) for j in range(n)] for i in range(n)]; self.edges=[]; seen=set()
        for e in edges:
            if e.left not in self.index or e.right not in self.index: raise Refused("FOREIGN_CORRELATION_ID")
            k=tuple(sorted((e.left,e.right)))
            if k in seen: raise Refused("DUPLICATE_CORRELATION_EDGE")
            seen.add(k); self.edges.append(e); i,j=self.index[e.left],self.index[e.right]; self.matrix[i][j]=self.matrix[j][i]=e.rho
