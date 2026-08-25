from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class OracleDifferential:
    support: int
    mean_absolute_gap: Fraction
    max_absolute_gap: Fraction


def differential(certificate, observations) -> OracleDifferential:
    obs = tuple(observations)
    if not obs:
        raise Refused("NO_ORACLE_OBSERVATIONS")
    gaps = [abs(item.oracle_cost - certificate.primal_value) for item in obs]
    return OracleDifferential(len(gaps), sum(gaps, Fraction(0, 1)) / len(gaps), max(gaps))
