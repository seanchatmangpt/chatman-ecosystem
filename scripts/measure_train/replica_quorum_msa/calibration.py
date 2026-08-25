from dataclasses import dataclass
from .metrics import measure_trials
@dataclass(frozen=True)
class CalibrationPolicy:
    min_support:int=12; max_false_current_rate:float=0.05; min_wilson_lower:float=0.70
def calibrate(trials,policy=CalibrationPolicy()):
    m=measure_trials(trials)
    if m.support<policy.min_support:return {"state":"INSUFFICIENT","metrics":m}
    fcr=m.false_current/m.support
    if fcr>policy.max_false_current_rate or m.wilson_lower<policy.min_wilson_lower:return {"state":"UNRELIABLE","metrics":m}
    return {"state":"CALIBRATED","metrics":m}
