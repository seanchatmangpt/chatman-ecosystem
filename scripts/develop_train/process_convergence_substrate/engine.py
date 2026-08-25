from dataclasses import dataclass
from .trajectory import Trajectory
from .dependency import DependencyGraph
from .obligation import State
from .policy import Strategy, classify
from .potential import potential_vector
from .hazard import hazards
from .pareto import Candidate, frontier
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    direction: str
    standing: str
    blockers: frozenset[str]
    candidates: tuple[Candidate, ...]
    receipt: Receipt


def _standing(traj: Trajectory, blockers: frozenset[str], direction: str) -> str:
    states=[o.state for o in traj.current.obligations]
    if any(s is State.FAIL for s in states): return "BUILD_BROKEN"
    if blockers or any(s is State.BLOCKED for s in states): return "BLOCKED"
    if direction != "CONVERGING" or any(s in (State.UNKNOWN,State.REFUSED) for s in states): return "UNKNOWN"
    return "PARTIAL_ALIVE"


def qualify(traj: Trajectory, graph: DependencyGraph, strategies=(Strategy.POTENTIAL,Strategy.HAZARD,Strategy.LYAPUNOV,Strategy.MINIMAX)) -> Qualification:
    blockers=graph.blocking_cut(traj.current)
    h=hazards(traj)
    raw=[]
    for s in strategies:
        d=classify(traj,s)
        debt=potential_vector(traj.current)[0]
        raw.append(Candidate(s.value,debt,h.regression,len(blockers)))
    pf=frontier(raw)
    selected=sorted(pf,key=lambda c:c.name)[0]
    strategy=Strategy(selected.name)
    direction=classify(traj,strategy)
    standing=_standing(traj,blockers,direction)
    r=Receipt(traj.current.subject.subject,traj.current.subject.generation,strategy.value,direction,standing)
    return Qualification(direction,standing,blockers,pf,r)
