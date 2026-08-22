from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from .calibration import CalibrationModel
from .subject import Refusal

@dataclass(frozen=True, slots=True)
class DriftVector:
    tpr_delta: Fraction
    fpr_delta: Fraction
    brier_delta: Fraction
    @property
    def l1(self)->Fraction:
        return abs(self.tpr_delta)+abs(self.fpr_delta)+abs(self.brier_delta)

def compare_models(previous:CalibrationModel,current:CalibrationModel)->DriftVector:
    if previous.source_id!=current.source_id: raise Refusal("REFUSED[FOREIGN_CALIBRATION_MODEL]")
    return DriftVector(current.tpr-previous.tpr,current.fpr-previous.fpr,current.brier-previous.brier)

def classify_drift(vector:DriftVector,*,threshold:Fraction)->str:
    if threshold<=0: raise Refusal("REFUSED[INVALID_DRIFT_THRESHOLD]")
    return "DRIFT" if vector.l1>=threshold else "STABLE"
