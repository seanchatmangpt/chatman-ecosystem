from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class ConsequenceError:
    support: int
    mean_absolute_error: Fraction
    bias: Fraction
    false_safe_rate: Fraction


def evaluate(observations) -> ConsequenceError:
    obs = tuple(observations)
    if not obs:
        raise Refused("NO_CONSEQUENCE_OBSERVATIONS")
    errors = [item.predicted_consequence_bound - item.realized_consequence for item in obs]
    abs_errors = [abs(value) for value in errors]
    false_safe = sum(item.predicted_consequence_bound < item.realized_consequence for item in obs)
    n = len(obs)
    return ConsequenceError(n, sum(abs_errors, Fraction(0,1))/n, sum(errors, Fraction(0,1))/n, Fraction(false_safe,n))
