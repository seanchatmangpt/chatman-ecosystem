from .belief import BeliefState
from .calibration import SensorCalibration
from .subject import Refused

def posterior(belief: BeliefState, calibration: SensorCalibration, outcome: str):
    if outcome not in {"PASS","FAIL"}:
        raise Refused("REFUSED[UNSUPPORTED_OUTCOME]")
    if outcome == "PASS":
        like_alive=calibration.sensitivity
        like_not=calibration.false_positive_rate
    else:
        like_alive=1-calibration.sensitivity
        like_not=1-calibration.false_positive_rate
    denom=belief.p_alive*like_alive + belief.p_not_alive*like_not
    if denom == 0:
        raise Refused("REFUSED[ZERO_PREDICTIVE_MASS]")
    return BeliefState((belief.p_alive*like_alive)/denom, belief.generation+1)
