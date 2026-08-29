from dataclasses import dataclass
from fractions import Fraction
from .calibration import CalibrationModel
from .subject import Refusal

@dataclass(frozen=True)
class DriftVector:
    tpr: Fraction
    fpr: Fraction
    brier: Fraction
    @property
    def l1(self) -> Fraction:
        return abs(self.tpr) + abs(self.fpr) + abs(self.brier)

def compare_models(previous: CalibrationModel, current: CalibrationModel) -> DriftVector:
    if previous.subject != current.subject or previous.source_id != current.source_id:
        raise Refusal('REFUSED[FOREIGN_CALIBRATION_MODEL]')
    return DriftVector(current.tpr-previous.tpr,current.fpr-previous.fpr,current.brier-previous.brier)

def classify_l1(vector: DriftVector, threshold: Fraction) -> str:
    if threshold <= 0: raise Refusal('REFUSED[INVALID_DRIFT_THRESHOLD]')
    return 'DRIFT' if vector.l1 >= threshold else 'STABLE'
