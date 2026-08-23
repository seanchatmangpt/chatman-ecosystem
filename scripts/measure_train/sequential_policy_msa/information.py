from fractions import Fraction
from math import log2
from .refusal import Refused

def cumulative_information(steps):
    predicted=sum((s.predicted_bits for s in steps), Fraction())
    realized=sum((s.realized_bits for s in steps), Fraction())
    return predicted, realized, realized-predicted

def efficiency(steps):
    realized=sum((s.realized_bits for s in steps), Fraction())
    cost=sum((s.cost for s in steps), Fraction())
    samples=sum(s.samples for s in steps)
    return {"bits_per_cost": None if cost == 0 else realized/cost,
            "bits_per_sample": None if samples == 0 else realized/Fraction(samples)}

def trajectory_entropy(weights):
    vals=[Fraction(w) for w in weights]
    total=sum(vals,Fraction())
    if total <= 0 or any(v < 0 for v in vals):
        raise Refused("REFUSED[INVALID_INFORMATION_WEIGHTS]")
    probs=[v/total for v in vals]
    return -sum(float(p)*log2(float(p)) for p in probs if p)
