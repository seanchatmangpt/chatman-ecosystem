from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from .errors import Refused
from .evidence import admit_log
from .support import importance_weight
class Estimator(StrEnum): IPS='IPS'; SNIPS='SNIPS'; DOUBLY_ROBUST='DOUBLY_ROBUST'
@dataclass(frozen=True, slots=True)
class Estimate: estimator:Estimator; value:Fraction
def estimate(rows,estimator):
    rows=admit_log(rows); ws=tuple(importance_weight(r) for r in rows)
    if estimator is Estimator.IPS: return Estimate(estimator,sum((w*r.reward for w,r in zip(ws,rows)),Fraction())/len(rows))
    if estimator is Estimator.SNIPS:
        total=sum(ws,Fraction())
        if total==0: raise Refused('REFUSED_ZERO_TARGET_MASS')
        return Estimate(estimator,sum((w*r.reward for w,r in zip(ws,rows)),Fraction())/total)
    if any(r.model_prediction is None for r in rows): raise Refused('REFUSED_MODEL_PROVENANCE_REQUIRED')
    return Estimate(estimator,sum((r.model_prediction+w*(r.reward-r.model_prediction) for w,r in zip(ws,rows)),Fraction())/len(rows))
