from fractions import Fraction
from .potential import weighted_debt
from .trajectory import Trajectory

def velocity(t: Trajectory) -> tuple[Fraction,...]:
    debts=[weighted_debt(e) for e in t.epochs]
    return tuple(b-a for a,b in zip(debts,debts[1:]))

def acceleration(t: Trajectory) -> tuple[Fraction,...]:
    v=velocity(t)
    return tuple(b-a for a,b in zip(v,v[1:]))
