from dataclasses import dataclass
from .trajectory import Trajectory
from .dependency import DependencyGraph
from .oscillation import oscillating_keys
from .standing import compute
from .strategy import Strategy
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    blockers: tuple[str,...]
    oscillations: tuple[str,...]
    receipt: Receipt

def qualify(t: Trajectory, graph: DependencyGraph, root: str, strategy: Strategy=Strategy.MINIMAX):
    blockers=graph.blocking_cut(root,t.current.states)
    oscillations=oscillating_keys(t)
    standing=compute(t.current.states,blockers,oscillations)
    receipt=Receipt(f"{t.current.subject.repo}@{t.current.subject.sha}",t.current.subject.generation,strategy.value,standing.value)
    return Qualification(standing.value,blockers,oscillations,receipt)
