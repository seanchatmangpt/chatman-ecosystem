import math
from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class GainCalibration:
    support: int
    mae_bits: float
    rmse_bits: float
    bias_bits: float
    status: str
def calibrate_gain(pairs,min_support=5,max_mae=0.25):
    rows=tuple((float(p),float(a)) for p,a in pairs)
    if any(p<0 or a<0 for p,a in rows): raise Refused("REFUSED[INVALID_GAIN_TRIAL]")
    if not rows: return GainCalibration(0,math.inf,math.inf,math.inf,"INSUFFICIENT")
    errors=[a-p for p,a in rows]; n=len(rows)
    mae=sum(abs(e) for e in errors)/n; rmse=math.sqrt(sum(e*e for e in errors)/n); bias=sum(errors)/n
    status="INSUFFICIENT" if n<min_support else ("CALIBRATED" if mae<=max_mae else "UNRELIABLE")
    return GainCalibration(n,mae,rmse,bias,status)
