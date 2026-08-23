from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True,order=True)
class CalibrationModel:
    generation:int
    digest:str
    support:int
    mae:Fraction
    state:str
def calibrate(observations,min_support=5,max_mae=Fraction(1,4)):
    rows=[o for o in observations if o.labeled]
    if not rows: return (0,Fraction(0),"INSUFFICIENT")
    errors=[abs(o.predicted_risk-(Fraction(0) if o.correct else Fraction(1))) for o in rows]
    mae=sum(errors,Fraction(0))/len(errors)
    state="INSUFFICIENT" if len(rows)<min_support else ("CALIBRATED" if mae<=max_mae else "UNRELIABLE")
    return (len(rows),mae,state)
def current(models):
    if not models: return None
    maxg=max(m.generation for m in models); rows=[m for m in models if m.generation==maxg]
    if len({m.digest for m in rows})!=1:
        from .subject import Refused
        raise Refused("REFUSED[DIVERGENT_CALIBRATION_FRONTIER]")
    return rows[0]
