from fractions import Fraction
from .trajectory import Trajectory
from .potential import potential_vector


def velocity(traj: Trajectory) -> tuple[Fraction, ...]:
    vals=[potential_vector(e)[0] for e in traj.epochs]
    return tuple(b-a for a,b in zip(vals,vals[1:]))


def acceleration(traj: Trajectory) -> tuple[Fraction, ...]:
    v=velocity(traj)
    return tuple(b-a for a,b in zip(v,v[1:]))
