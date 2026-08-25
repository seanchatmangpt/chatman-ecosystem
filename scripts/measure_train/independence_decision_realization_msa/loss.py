from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class LossRealization:
    support:int; total_loss:Fraction; mean_loss:Fraction; max_loss:Fraction
def realized_loss(policy,rows):
    values=tuple(policy.realized_loss(r.decision,r.truth) for r in rows)
    if not values: return LossRealization(0,Fraction(0),Fraction(0),Fraction(0))
    total=sum(values,Fraction(0))
    return LossRealization(len(values),total,total/len(values),max(values))
