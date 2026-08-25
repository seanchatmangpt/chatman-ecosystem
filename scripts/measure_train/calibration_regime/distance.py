from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

@dataclass(frozen=True)
class DriftVector:
    delta_tpr: Fraction
    delta_fpr: Fraction
    delta_brier: Fraction
    @property
    def max_delta(self):
        return max(self.delta_tpr,self.delta_fpr,self.delta_brier)

def model_distance(reference, current):
    if reference.subject != current.subject: raise Refused("REFUSED[FOREIGN_MODEL_SUBJECT]")
    if reference.source_id != current.source_id: raise Refused("REFUSED[FOREIGN_MODEL_SOURCE]")
    return DriftVector(abs(current.tpr-reference.tpr),abs(current.fpr-reference.fpr),abs(current.brier-reference.brier))

def classify_distance(reference, current, threshold=Fraction(1,4)):
    if threshold <= 0 or threshold > 1: raise Refused("REFUSED[INVALID_DRIFT_THRESHOLD]")
    return "DRIFT" if model_distance(reference,current).max_delta >= threshold else "STABLE"
