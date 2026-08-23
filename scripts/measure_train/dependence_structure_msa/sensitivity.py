from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class DependenceSensitivity:
    conservative_lower:Fraction
    independent_lower:Fraction
    lower_gain:Fraction
    upper_gain:Fraction

def compare(a_lower,a_upper,b_lower,b_upper):
    conservative_lower=max(Fraction(0),a_lower+b_lower-1)
    conservative_upper=min(a_upper,b_upper)
    independent_lower=a_lower*b_lower
    independent_upper=a_upper*b_upper
    return DependenceSensitivity(
      conservative_lower,independent_lower,
      independent_lower-conservative_lower,
      independent_upper-conservative_upper,
    )
