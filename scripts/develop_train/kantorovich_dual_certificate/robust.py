from dataclasses import dataclass
from fractions import Fraction
from .measure import FiniteMeasure
from .errors import Refused
@dataclass(frozen=True)
class WorstCase:
    value: Fraction
    witness: FiniteMeasure
    distance: Fraction
    certificate_gap: Fraction

def _compositions(total, count, prefix=()):
    if count == 1:
        yield prefix + (total,); return
    for value in range(total + 1):
        yield from _compositions(total - value, count - 1, prefix + (value,))

def worst_case(ambiguity, losses, denominator=12, max_states=100000):
    support = ambiguity.center.support
    if denominator <= 0:
        raise Refused("INVALID_SIMPLEX_DENOMINATOR")
    best = None; states = 0
    for counts in _compositions(denominator, len(support)):
        states += 1
        if states > max_states:
            raise Refused("ROBUST_STATE_SPACE_LIMIT")
        candidate = FiniteMeasure.from_mapping({key: Fraction(count, denominator) for key, count in zip(support, counts) if count})
        cert = ambiguity.certificate(candidate)
        if cert.primal_value <= ambiguity.radius:
            item = WorstCase(candidate.expectation(losses), candidate, cert.primal_value, cert.gap)
            if best is None or (item.value, item.witness.mass) > (best.value, best.witness.mass):
                best = item
    if best is None:
        raise Refused("EMPTY_AMBIGUITY_LATTICE")
    return best
