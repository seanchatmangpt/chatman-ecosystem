from fractions import Fraction
from .epoch import ClosureEpoch

def weighted_debt(epoch: ClosureEpoch) -> Fraction:
    return sum((o.weight * int(o.state) for o in epoch.obligations), Fraction(0,1))

def max_severity(epoch: ClosureEpoch) -> int:
    return max((int(o.state) for o in epoch.obligations), default=0)

def lexicographic(epoch: ClosureEpoch) -> tuple[int,...]:
    return tuple(sorted((int(o.state) for o in epoch.obligations), reverse=True))

def potential_vector(epoch: ClosureEpoch):
    return weighted_debt(epoch), max_severity(epoch), lexicographic(epoch)
