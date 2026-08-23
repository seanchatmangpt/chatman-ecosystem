from dataclasses import dataclass
from .confusion import confusion
from .relation import Relation
from .wilson import wilson_lower

@dataclass(frozen=True)
class RelationCalibration:
    relation: Relation
    support: int
    precision: float
    recall: float
    false_positive_rate: float
    lower_accuracy: float
    state: str

def calibrate(cases, relation, min_support=4, max_fp=0.10, min_lower_accuracy=0.45):
    c=confusion(cases,relation)
    correct=c.true_accept+c.true_refuse
    lower=wilson_lower(correct,c.support)
    fp=float(c.false_positive_rate)
    state=("INSUFFICIENT" if c.support<min_support else
           "UNRELIABLE" if fp>max_fp or lower<min_lower_accuracy else "CALIBRATED")
    return RelationCalibration(relation,c.support,float(c.precision),float(c.recall),fp,lower,state)
