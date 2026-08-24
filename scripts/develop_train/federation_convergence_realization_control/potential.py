from dataclasses import dataclass
@dataclass(frozen=True, order=True)
class Potential:
    blockers: int
    errors: int
    churn: int
def potential(o): return Potential(o.realized_blockers,o.realized_errors,o.realized_churn)
def descending(a,b): return potential(b) < potential(a)
def descent_fraction(trajectory):
    pairs=list(zip(trajectory.observations,trajectory.observations[1:]))
    return sum(descending(a,b) for a,b in pairs)/len(pairs) if pairs else 1.0
