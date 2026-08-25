from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class TransportPlan:
    flow:tuple
    @classmethod
    def of(cls,flow):
        rows=[]
        for a,b,x in flow:
            q=Fraction(x)
            if q<0: raise Refused("NEGATIVE_FLOW")
            if q: rows.append((str(a),str(b),q))
        return cls(tuple(sorted(rows)))
    def verify_marginals(self,source,target):
        s={k:Fraction() for k in source.support}; t={k:Fraction() for k in target.support}
        for a,b,x in self.flow:
            if a not in s or b not in t: raise Refused("PLAN_SUPPORT_GAP")
            s[a]+=x; t[b]+=x
        if s!=source.as_dict() or t!=target.as_dict(): raise Refused("MARGINAL_MISMATCH")
        return True
    def cost(self,metric): return sum((x*metric.cost(a,b) for a,b,x in self.flow),Fraction())
