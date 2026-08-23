from dataclasses import dataclass
from .subject import Subject
from .sensor import Sensor,Observation
from .independence import IndependenceProof,admitted_pairs,maximum_independent_subset
from .fusion import robust_current_score
from .currentness import CalibrationFrontier,require_current
from .topology import classify
from .acquisition import AcquisitionCandidate,Budget,select
from .pareto import frontier as pareto_frontier
from .authority import ActionClass,admit_action
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    topology:str
    standing:str
    selected_candidate:str|None
    pareto:tuple[str,...]
    receipt:Receipt

def qualify(subject:Subject,sensors:list[Sensor],observations:list[Observation],proofs:list[IndependenceProof],expected_frontier:CalibrationFrontier,candidates:list[AcquisitionCandidate],budget:Budget,strategy:str,action:ActionClass=ActionClass.CONSTRUCT)->Qualification:
    admit_action(action); require_current(sensors,expected_frontier)
    pairs=admitted_pairs(sensors,proofs); independent=maximum_independent_subset(sensors,pairs)
    score=robust_current_score(sensors,observations,set(independent)); topo=classify(score,len(independent))
    selected=None
    if topo.state in {"AMBIGUOUS","UNDER_SUPPORTED"} and candidates:
        selected=select(candidates,budget,strategy).candidate_id
    standing="PARTIAL_ALIVE" if topo.state=="CURRENT" else "UNKNOWN"
    receipt=Receipt(subject.identity,expected_frontier.generation,topo.state,strategy,selected,standing)
    return Qualification(topo.state,standing,selected,pareto_frontier(candidates),receipt)
