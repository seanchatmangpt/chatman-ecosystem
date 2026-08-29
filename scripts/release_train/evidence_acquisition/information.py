from fractions import Fraction
from math import log2

from .belief import Belief
from .calibration import SensorCalibration

def pass_probability(belief: Belief, calibration: SensorCalibration) -> Fraction:
    return belief.defect * (1 - calibration.tpr) + (1 - belief.defect) * (1 - calibration.fpr)

def posterior_defect(belief: Belief, calibration: SensorCalibration, outcome: str) -> Fraction:
    if outcome not in {"PASS", "FAIL"}:
        raise ValueError("REFUSED[INVALID_EVIDENCE_OUTCOME]")
    if outcome == "FAIL":
        numerator = belief.defect * calibration.tpr
        denominator = numerator + (1 - belief.defect) * calibration.fpr
    else:
        numerator = belief.defect * (1 - calibration.tpr)
        denominator = numerator + (1 - belief.defect) * (1 - calibration.fpr)
    if denominator == 0:
        raise ValueError("REFUSED[ZERO_PREDICTIVE_MASS]")
    return numerator / denominator

def binary_entropy(p: Fraction) -> float:
    value = float(p)
    if value in {0.0, 1.0}:
        return 0.0
    return -(value * log2(value) + (1 - value) * log2(1 - value))

def expected_information_gain(belief: Belief, calibration: SensorCalibration) -> float:
    p_pass = pass_probability(belief, calibration)
    p_fail = 1 - p_pass
    expected = float(p_pass) * binary_entropy(posterior_defect(belief, calibration, "PASS"))
    expected += float(p_fail) * binary_entropy(posterior_defect(belief, calibration, "FAIL"))
    return max(0.0, binary_entropy(belief.defect) - expected)
