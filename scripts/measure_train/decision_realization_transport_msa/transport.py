from fractions import Fraction
from .errors import Refused
def transported_risk(observations,weights):
    rows=[o for o in observations if o.stratum in weights]
    if not rows: raise Refused("REFUSED[NO_TRANSPORT_SUPPORT]")
    num=sum((weights[o.stratum]*o.realized_loss for o in rows),Fraction(0))
    den=sum((weights[o.stratum] for o in rows),Fraction(0))
    if den==0: raise Refused("REFUSED[ZERO_TRANSPORT_WEIGHT]")
    return num/den
