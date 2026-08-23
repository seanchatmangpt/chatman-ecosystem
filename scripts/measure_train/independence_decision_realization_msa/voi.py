from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True, order=True)
class DeferRealization:
    decision_id:str; pre_risk:Fraction; post_risk:Fraction; information_cost:Fraction; latency_cost:Fraction; acquired:bool
    def __post_init__(self):
        if any(x<0 for x in (self.pre_risk,self.post_risk,self.information_cost,self.latency_cost)): raise Refused("REFUSED[NEGATIVE_VOI_TERM]")
    @property
    def realized_value(self):
        return self.pre_risk-self.post_risk-self.information_cost-self.latency_cost if self.acquired else Fraction(0)
def realized_voi(rows):
    vals=[r.realized_value for r in rows if r.acquired]
    return {"support":len(vals),"mean_value":sum(vals,Fraction(0))/len(vals) if vals else Fraction(0),"positive_rate":Fraction(sum(1 for v in vals if v>0),len(vals)) if vals else Fraction(0)}
