from fractions import Fraction
from .refusal import Refused

def forecast_calibration(steps,min_support=3,max_mae=Fraction(1,2)):
    if min_support < 1:
        raise Refused("REFUSED[INVALID_SUPPORT_FLOOR]")
    if len(steps) < min_support:
        return {"state":"INSUFFICIENT","support":len(steps),"mae":None,"bias":None}
    errors=[s.realized_bits-s.predicted_bits for s in steps]
    mae=sum((abs(e) for e in errors),Fraction())/len(errors)
    bias=sum(errors,Fraction())/len(errors)
    state="CALIBRATED" if mae <= max_mae else "UNRELIABLE"
    return {"state":state,"support":len(steps),"mae":mae,"bias":bias}
