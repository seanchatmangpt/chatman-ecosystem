from fractions import Fraction
from .errors import Refused

def loss(obs, false_independent=Fraction(5), false_dependent=Fraction(1), defer=Fraction(1,2)):
    if obs.decision == "DEFER": return defer + obs.realized_cost
    if obs.decision == obs.truth: return obs.realized_cost
    return (false_independent if obs.decision=="INDEPENDENT" else false_dependent) + obs.realized_cost

def horvitz_thompson(observations, losses):
    if len(observations)!=len(losses) or not observations: raise Refused("RISK_INPUT_MISMATCH")
    return sum((l/o.propensity for o,l in zip(observations,losses)), Fraction(0))/len(observations)

def self_normalized(observations, losses):
    ws=[1/o.propensity for o in observations]
    denom=sum(ws,Fraction(0))
    if denom==0: raise Refused("ZERO_WEIGHT_SUPPORT")
    return sum((w*l for w,l in zip(ws,losses)),Fraction(0))/denom
