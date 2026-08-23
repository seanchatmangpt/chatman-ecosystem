from dataclasses import dataclass
from datetime import datetime
from .acquisition import Strategy,select
from .authority import ActionClass,admit_action
from .dependency import DependencyGraph
from .errors import Refused
from .frontier import frontier,require_current
from .fusion import robust_fuse
from .independence import maximum_independent_subset
from .pareto import frontier as pareto_frontier
from .receipt import Receipt
from .standing import bounded_standing
from .topology import FusionTopology,classify

@dataclass(frozen=True)
class Qualification:
    receipt:Receipt
    selected_acquisition:str|None
    pareto_candidates:tuple[str,...]

def qualify(*,subject,calibrations,observations,independence_proofs,candidates,dependencies:DependencyGraph,now:datetime,strategy=Strategy.MAX_INFORMATION,max_observation_age_seconds=300,action=ActionClass.SELECT):
    admit_action(action)
    if not calibrations or not observations: raise Refused("MISSING_FUSION_EVIDENCE")
    if any(c.sensor.subject!=subject for c in calibrations): raise Refused("CALIBRATION_SUBJECT_MISMATCH")
    if any(o.subject!=subject for o in observations): raise Refused("OBSERVATION_SUBJECT_MISMATCH")
    evidence_ids=[o.evidence_id for o in observations]
    if len(evidence_ids)!=len(set(evidence_ids)): raise Refused("DUPLICATE_OBSERVATION")
    for o in observations: o.require_current(now,max_observation_age_seconds)
    current=frontier(calibrations)
    for c in calibrations: require_current(c,current)
    independent=maximum_independent_subset([c.sensor for c in calibrations],independence_proofs)
    try:
        fused=robust_fuse(observations,calibrations,independent)
        topology=classify(calibrations,observations,independent,fused)
    except Refused as exc:
        if exc.code=="INSUFFICIENT_INDEPENDENT_SENSORS": topology=FusionTopology.CORRELATED
        else: raise
    blockers=dependencies.blockers(subject)
    standing,reason=bounded_standing(topology,blockers)
    pf=pareto_frontier(candidates); chosen=None
    if standing!="PARTIAL_ALIVE" and not blockers:
        chosen=select(pf,strategy)
        if chosen is None: raise Refused("NO_BOUNDED_ACQUISITION_CANDIDATE")
    receipt=Receipt(subject=subject.canonical(),calibration_generation=current.generation,topology=topology.value,standing=standing,blockers=blockers,selected_acquisition=chosen.candidate_id if chosen else None,strategy=strategy.value if chosen else None).seal()
    receipt.replay()
    return Qualification(receipt,chosen.candidate_id if chosen else None,tuple(sorted(c.candidate_id for c in pf)))
