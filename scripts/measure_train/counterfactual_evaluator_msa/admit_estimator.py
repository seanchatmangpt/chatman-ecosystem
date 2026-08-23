from fractions import Fraction
from .refusal import Refused
from .currentness import require_current

def admit_estimator(model,frontier,weight_diag,sensitivity,max_mae=Fraction(1,4),min_ess=Fraction(2),max_weight_ratio=Fraction(4),max_sensitivity=Fraction(1,3)):
    require_current(model,frontier)
    c=model.calibration
    if c.state=="INSUFFICIENT": raise Refused("REFUSED[UNDERCALIBRATED_ESTIMATOR]")
    if c.state!="CALIBRATED" or c.mae>max_mae: raise Refused("REFUSED[UNRELIABLE_ESTIMATOR]")
    if weight_diag.ess < min_ess: raise Refused("REFUSED[DEGENERATE_EFFECTIVE_SAMPLE]")
    if weight_diag.max_to_mean > max_weight_ratio: raise Refused("REFUSED[WEIGHT_CONCENTRATION]")
    if sensitivity.max_shift > max_sensitivity: raise Refused("REFUSED[ESTIMATOR_SENSITIVITY]")
    return "ADMITTED"
