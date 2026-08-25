from fractions import Fraction
from .errors import Refused

def realized_defer_value(pre_risk: Fraction, post_risk: Fraction, acquisition_cost: Fraction, latency_cost: Fraction):
    if min(pre_risk,post_risk,acquisition_cost,latency_cost)<0:
        raise Refused("NEGATIVE_DEFER_COMPONENT")
    return pre_risk-post_risk-acquisition_cost-latency_cost
