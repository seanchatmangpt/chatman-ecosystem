from fractions import Fraction
from .subject import Refused

def brier_score(predicted_pass: Fraction, outcome: str) -> Fraction:
    if not (Fraction(0) <= predicted_pass <= Fraction(1)):
        raise Refused("REFUSED[INVALID_PREDICTIVE_MASS]")
    if outcome not in {"PASS","FAIL"}:
        raise Refused("REFUSED[UNSCORABLE_OUTCOME]")
    actual=Fraction(1) if outcome=="PASS" else Fraction(0)
    d=predicted_pass-actual
    return d*d
