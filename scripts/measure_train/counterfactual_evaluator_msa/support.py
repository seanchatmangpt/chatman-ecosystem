from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class SupportProfile:
    n: int
    covered: int
    positivity_rate: Fraction
    target_mass: Fraction

def support_profile(cases):
    if not cases: return SupportProfile(0,0,Fraction(0),Fraction(0))
    covered=sum(1 for c in cases if c.target_propensity==0 or c.behavior_propensity>0)
    return SupportProfile(len(cases),covered,Fraction(covered,len(cases)),sum((c.target_propensity for c in cases),Fraction(0)))

def require_support(profile, min_cases):
    if min_cases < 1: raise Refused("REFUSED[INVALID_SUPPORT_FLOOR]")
    if profile.n < min_cases: raise Refused("REFUSED[INSUFFICIENT_SUPPORT]")
    if profile.covered != profile.n: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
    return "ADMITTED"
