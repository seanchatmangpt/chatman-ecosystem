from fractions import Fraction
from .subject import Refused
from .loss import realized_loss
def horvitz_thompson(observations,matrix):
    rows=tuple(observations)
    if not rows: raise Refused("REFUSED[EMPTY_RISK_SAMPLE]")
    total=sum((realized_loss(o,matrix)/o.propensity for o in rows if o.labeled),Fraction(0))
    return total/len(rows)
def self_normalized(observations,matrix):
    rows=tuple(o for o in observations if o.labeled)
    if not rows: raise Refused("REFUSED[EMPTY_RISK_SAMPLE]")
    weights=[Fraction(1,o.propensity) for o in rows]
    den=sum(weights,Fraction(0))
    return sum((w*realized_loss(o,matrix) for w,o in zip(weights,rows)),Fraction(0))/den
