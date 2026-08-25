from .belief import BeliefState
from .calibration import SensorCalibration

def predictive_pass_probability(belief: BeliefState, calibration: SensorCalibration):
    return belief.p_alive*calibration.sensitivity + belief.p_not_alive*calibration.false_positive_rate

def predictive_distribution(belief, calibration):
    p=predictive_pass_probability(belief, calibration)
    return {"PASS":p, "FAIL":1-p}
