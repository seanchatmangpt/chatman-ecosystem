from __future__ import annotations
from dataclasses import dataclass
import math
from .admission import RecoveryWitness
from .calibration import CalibrationModel
from .subject import Refusal
@dataclass(frozen=True,slots=True)
class InformationContribution:
    source_id:str; value:float
def contribution(model:CalibrationModel,witness:RecoveryWitness)->InformationContribution:
    if model.source_id!=witness.source_id: raise Refusal("REFUSED[CALIBRATION_SOURCE_MISMATCH]")
    if witness.outcome in {"PENDING","UNKNOWN","UNSUPPORTED"}: return InformationContribution(witness.source_id,0.0)
    tpr=float(model.tpr); fpr=float(model.fpr)
    if witness.outcome=="PASS": value=math.log(tpr/fpr)
    elif witness.outcome=="FAIL": value=math.log((1.0-tpr)/(1.0-fpr))
    else: raise Refusal("REFUSED[INVALID_WITNESS_OUTCOME]")
    if not math.isfinite(value): raise Refusal("REFUSED[NONFINITE_INFORMATION]")
    return InformationContribution(witness.source_id,value)
