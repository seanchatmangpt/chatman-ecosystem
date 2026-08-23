from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class SensitivityProfile:
    baseline: Fraction
    perturbed: tuple
    max_shift: Fraction
    mean_shift: Fraction

def sensitivity_profile(baseline, perturbed):
    ps=tuple(perturbed)
    if not ps: raise Refused("REFUSED[EMPTY_SENSITIVITY_SET]")
    shifts=tuple(abs(x-baseline) for x in ps)
    return SensitivityProfile(baseline,ps,max(shifts),sum(shifts,Fraction(0))/len(shifts))
