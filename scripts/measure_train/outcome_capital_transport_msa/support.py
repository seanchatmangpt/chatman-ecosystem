from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True)
class SupportProfile:
    total:int
    labeled:int
    missing:int
    ess:Fraction
    max_weight:Fraction
    missing_rate:Fraction
def profile(observations):
    rows=tuple(observations); weights=[Fraction(1,o.propensity) for o in rows if o.labeled]
    total=len(rows); labeled=len(weights); missing=total-labeled
    if not weights:
        ess=Fraction(0); maxw=Fraction(0)
    else:
        s=sum(weights,Fraction(0)); sq=sum((w*w for w in weights),Fraction(0))
        ess=s*s/sq if sq else Fraction(0); maxw=max(weights)
    return SupportProfile(total,labeled,missing,ess,maxw,Fraction(missing,total) if total else Fraction(1))
def require_support(p,min_labeled=5,min_ess=Fraction(3),max_missing=Fraction(2,5),max_weight=Fraction(20)):
    if p.labeled < min_labeled: raise Refused("REFUSED[INSUFFICIENT_LABELED_SUPPORT]")
    if p.ess < min_ess: raise Refused("REFUSED[INSUFFICIENT_EFFECTIVE_SAMPLE]")
    if p.missing_rate > max_missing: raise Refused("REFUSED[EXCESSIVE_MISSINGNESS]")
    if p.max_weight > max_weight: raise Refused("REFUSED[WEIGHT_CONCENTRATION]")
    return True
