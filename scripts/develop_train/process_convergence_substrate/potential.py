from fractions import Fraction
from .epoch import ClosureEpoch


def potential_vector(epoch: ClosureEpoch) -> tuple[Fraction, int, tuple[int, ...]]:
    obligations=epoch.obligations
    total=sum((o.weight for o in obligations), Fraction(0,1))
    weighted=sum((o.weight * int(o.state) for o in obligations), Fraction(0,1))
    l1=weighted / total if total else Fraction(0,1)
    max_severity=max((int(o.state) for o in obligations), default=0)
    lex=tuple(sorted((int(o.state) for o in obligations), reverse=True))
    return l1, max_severity, lex
