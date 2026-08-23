from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class DualPotential:
    source:tuple; target:tuple
    @classmethod
    def of(cls,source,target):
        return cls(tuple(sorted((str(k),Fraction(v)) for k,v in source.items())),tuple(sorted((str(k),Fraction(v)) for k,v in target.items())))
    def objective(self,p,q):
        u=dict(self.source); v=dict(self.target)
        if set(u)!=set(p.support) or set(v)!=set(q.support): raise Refused("DUAL_SUPPORT_GAP")
        return sum((p.as_dict()[k]*u[k] for k in p.support),Fraction())+sum((q.as_dict()[k]*v[k] for k in q.support),Fraction())
    def require_feasible(self,metric):
        for a,ua in self.source:
            for b,vb in self.target:
                if ua+vb>metric.cost(a,b): raise Refused("DUAL_INFEASIBLE",f"{a}->{b}")
        return True
