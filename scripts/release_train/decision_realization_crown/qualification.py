from dataclasses import dataclass
from .admission import admit
from .calibration import calibration_mae
from .methodology import require_methodologies
from .strata import require_strata
from .engine import require_engines
from .oracles import require_oracles
from .distribution import require_distribution
from .failures import require_failures
from .dependency import blockers as dep_blockers
from .receipt import Receipt
from .standing import compute
@dataclass(frozen=True)
class RealizationModel:
    generation:int; digest:str
@dataclass(frozen=True)
class Qualification:
    standing:str; reason:str; blockers:tuple; receipt:object
def qualify(*,subject,policy,observations,calibration,drift,engines,oracles,regions,failure_worlds,dependency_graph,dependency_standing,root="release"):
    obs=admit(policy,observations); calibration.admitted(); mae=calibration_mae(policy,obs)
    if mae>calibration.max_mae: return Qualification("UNKNOWN","REALIZED_CALIBRATION_UNRELIABLE",(),None)
    if drift.changed: return Qualification("UNKNOWN","REALIZED_RISK_DRIFT",(),None)
    bs=dep_blockers(dependency_graph,dependency_standing,root)
    if bs: return Qualification("BLOCKED","DEPENDENCY_BLOCKER",bs,None)
    require_strata(policy,obs,calibration.max_mae); require_methodologies(obs); require_engines(engines); require_oracles(oracles); require_distribution(regions); require_failures(failure_worlds)
    standing=compute(blockers=bs,drift=False,calibration_ok=True,global_ok=True)
    body={"schema":"chatman.decision-realization-crown/1","subject":subject.key,"policy_generation":policy.generation,"policy_digest":policy.digest,"standing":standing,"blockers":list(bs),"authority":"SELECT","phases":["VERIFY","CONSTRUCT"],"actuation_performed":False}
    return Qualification(standing,"REALIZED_CONSEQUENCE_QUALIFIED",bs,Receipt.make(body))
