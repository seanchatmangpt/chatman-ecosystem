import math
from fractions import Fraction
from .belief import BeliefState
from .predictive import predictive_distribution
from .posterior import posterior

def binary_entropy(p: Fraction):
    if p in (0,1): return 0.0
    x=float(p)
    return -(x*math.log2(x)+(1-x)*math.log2(1-x))

def expected_information_gain(belief, calibration):
    before=binary_entropy(belief.p_alive)
    dist=predictive_distribution(belief,calibration)
    after=0.0
    for outcome,prob in dist.items():
        if prob:
            after += float(prob)*binary_entropy(posterior(belief,calibration,outcome).p_alive)
    gain=before-after
    return 0.0 if abs(gain) < 1e-15 else gain
