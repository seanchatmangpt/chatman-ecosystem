from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class DependenceSensitivity:
    conservative_width: Fraction
    independent_width: Fraction
    endpoint_shift: Fraction
def sensitivity(conservative,independent):
    shift=max(abs(conservative.lower-independent.lower),abs(conservative.upper-independent.upper))
    return DependenceSensitivity(conservative.width,independent.width,shift)
