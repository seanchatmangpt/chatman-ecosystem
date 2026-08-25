from .confusion import confusion
from .loss import realized_loss
from .selective_risk import selective_risk
from .calibration import calibrate
from .wilson import error_upper

def census(policy,rows):
    c=confusion(rows); l=realized_loss(policy,rows); s=selective_risk(rows); cal=calibrate(rows)
    return {"support":c.support,"correct":c.correct,"false_independent":c.false_independent,"false_dependent":c.false_dependent,"deferred":c.deferred,"mean_loss":l.mean_loss,"coverage":s.coverage,"conditional_error":s.conditional_error,"brier":cal.brier,"calibration_state":cal.state,"error_wilson_upper":error_upper(c)}
