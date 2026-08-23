from fractions import Fraction
from .refusal import Refused

def page_hinkley(steps,delta=Fraction(1,20),threshold=Fraction(1,1)):
    if delta < 0 or threshold <= 0:
        raise Refused("REFUSED[INVALID_CHANGE_DETECTOR]")
    mean=Fraction(); cum=Fraction(); minimum=Fraction(); drift=False
    for n,s in enumerate(steps,1):
        x=s.realized_bits-s.predicted_bits
        mean += (x-mean)/n
        cum += x-mean-delta
        minimum=min(minimum,cum)
        if cum-minimum > threshold:
            drift=True
    return {"drift":drift,"mean_residual":mean,"score":cum-minimum}
