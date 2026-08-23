from dataclasses import dataclass
from fractions import Fraction
from .refusal import refuse

@dataclass(frozen=True)
class SupportProfile:
    support: int
    ess: Fraction
    max_to_mean: Fraction

def weights(rows): return tuple(r.target_propensity/r.behavior_propensity for r in rows)

def profile(rows):
    ws=weights(rows); n=len(ws); total=sum(ws,Fraction(0)); sq=sum((w*w for w in ws),Fraction(0))
    if total<=0 or sq<=0: refuse("ZERO_TARGET_MASS")
    ess=total*total/sq
    mean=total/n
    return SupportProfile(n,ess,max(ws)/mean)

def require_support(p, *, min_support=3, min_ess=Fraction(2), max_concentration=Fraction(4)):
    if p.support < min_support: refuse("INSUFFICIENT_SUPPORT")
    if p.ess < min_ess: refuse("DEGENERATE_EFFECTIVE_SAMPLE")
    if p.max_to_mean > max_concentration: refuse("EXCESSIVE_WEIGHT_CONCENTRATION")
    return p
