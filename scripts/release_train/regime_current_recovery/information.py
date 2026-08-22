from dataclasses import dataclass
import math
from .calibration import CalibrationModel
from .subject import Refusal

@dataclass(frozen=True)
class InformationContribution:
    outcome: str
    value: float

def contribution(model: CalibrationModel, outcome: str) -> InformationContribution:
    if outcome in {'PENDING','UNKNOWN','UNSUPPORTED'}: return InformationContribution(outcome,0.0)
    if outcome not in {'PASS','FAIL'}: raise Refusal('REFUSED[INVALID_WITNESS_OUTCOME]')
    tpr,fpr=float(model.tpr),float(model.fpr); eps=1e-12
    value=math.log(max(tpr,eps)/max(fpr,eps)) if outcome=='PASS' else math.log(max(1-tpr,eps)/max(1-fpr,eps))
    return InformationContribution(outcome,round(value,12))

def sequential_decision(values: list[InformationContribution], accept: float=2.0, reject: float=-2.0) -> tuple[str,float]:
    if reject>=accept: raise Refusal('REFUSED[INVALID_DECISION_THRESHOLDS]')
    statistic=round(sum(v.value for v in values),12)
    if statistic>=accept: return 'ACCEPT_BOUNDED',statistic
    if statistic<=reject: return 'REJECT',statistic
    return 'CONTINUE',statistic
