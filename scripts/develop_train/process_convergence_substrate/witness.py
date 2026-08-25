from dataclasses import dataclass
from .trajectory import Trajectory
from .potential import potential_vector
from .dwell import dwell

@dataclass(frozen=True)
class LyapunovWitness:
    nonincreasing: bool
    strictly_decreased: bool

@dataclass(frozen=True)
class FixedPointWitness:
    repeated_state: bool
    pass_dwell: int


def lyapunov_witness(traj: Trajectory) -> LyapunovWitness:
    vals=[potential_vector(e)[0] for e in traj.epochs]
    return LyapunovWitness(all(b<=a for a,b in zip(vals,vals[1:])), any(b<a for a,b in zip(vals,vals[1:])))


def fixed_point_witness(traj: Trajectory) -> FixedPointWitness:
    states=[tuple((o.key,int(o.state)) for o in e.obligations) for e in traj.epochs]
    return FixedPointWitness(len(states)>=2 and states[-1] == states[-2], dwell(traj))
